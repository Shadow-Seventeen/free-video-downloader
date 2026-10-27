#!/usr/bin/env python3
"""B站 UP 主视频同步：批量补下载 + 每日检查新视频，自动跳过充电专属/付费视频。

用法:
  .venv/bin/python bili_sync.py --sync                 # 补下载所有未下载的非充电视频
  .venv/bin/python bili_sync.py --sync --dry-run       # 只列出将要下载的视频
  .venv/bin/python bili_sync.py --check                # 检查并下载新视频（定时任务调用）
  .venv/bin/python bili_sync.py --install-schedule 09:00
  .venv/bin/python bili_sync.py --uninstall-schedule
"""

import argparse
import fcntl
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import datetime

import httpx
import yt_dlp
from yt_dlp.utils import sanitize_filename

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
COOKIE_FILE = os.path.join(BACKEND_DIR, "bilibili_cookies.txt")
DEFAULT_MID = "351413419"
DEFAULT_OUT_DIR = "/Users/shadow/Downloads/野生量化员"

PLIST_LABEL = "com.wildquant.bili-sync"
PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{PLIST_LABEL}.plist")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# 插电、或电池电量高于该阈值时，下载期间阻止系统空闲睡眠；否则允许休眠
BATTERY_FLOOR_PCT = 30
KEEP_AWAKE_CHECK_SECONDS = 30
KEEP_AWAKE_ASSERTION_SECONDS = 60  # 比检查间隔长，保证断言无缝衔接

# launchd 在暗唤醒（DarkWake）里启动时 Wi-Fi/DNS 可能还没就绪，先等网络
NETWORK_WAIT_ATTEMPTS = 30
NETWORK_WAIT_SECONDS = 20


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def power_status():
    """返回 (是否插电, 电量百分比)。查询失败时按未插电、0% 处理。"""
    try:
        out = subprocess.run(["pmset", "-g", "batt"], capture_output=True,
                             text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return False, 0
    on_ac = "'AC Power'" in out
    m = re.search(r"(\d+)%", out)
    return on_ac, int(m.group(1)) if m else 0


def keep_awake_loop():
    """下载期间按电源状态维持防睡眠断言，供后台线程使用。"""
    if not shutil.which("caffeinate"):
        return
    holding = None
    while True:
        on_ac, pct = power_status()
        should_hold = on_ac or pct > BATTERY_FLOOR_PCT
        if should_hold != holding:
            if should_hold:
                why = "已插电" if on_ac else f"电池 {pct}%"
                log(f"下载期间阻止系统睡眠（{why}）")
            else:
                log(f"允许系统睡眠（电池 {pct}%，未插电）")
            holding = should_hold
        if should_hold:
            # 断言带超时，循环内反复续期；退出或掉电后自动失效
            subprocess.Popen(["caffeinate", "-i", "-t", str(KEEP_AWAKE_ASSERTION_SECONDS)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(KEEP_AWAKE_CHECK_SECONDS)


def state_path(mid):
    return os.path.join(DATA_DIR, f"bili_sync_{mid}.json")


def load_state(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            pass
    return {"videos": {}}


def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def acquire_lock():
    os.makedirs(DATA_DIR, exist_ok=True)
    f = open(os.path.join(DATA_DIR, "bili_sync.lock"), "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("已有同步任务在运行，本次退出")
        sys.exit(0)
    f.write(str(os.getpid()))
    f.flush()
    return f


def buvid_cookies():
    cookies = {}
    if not os.path.exists(COOKIE_FILE):
        return cookies
    with open(COOKIE_FILE, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) >= 7 and p[5] in ("buvid3", "b_nut"):
                cookies[p[5]] = p[6]
    return cookies


def network_ready(timeout=5):
    try:
        socket.create_connection(("api.bilibili.com", 443), timeout=timeout).close()
        return True
    except OSError:
        return False


def wait_for_network():
    """暗唤醒刚起来时 DNS/Wi-Fi 往往还没就绪，先等网络可用再发请求。

    系统若在这期间回睡，进程会被挂起，下次维护唤醒后继续重试。
    """
    for attempt in range(1, NETWORK_WAIT_ATTEMPTS + 1):
        if network_ready():
            if attempt > 1:
                log(f"网络已就绪（等待 {(attempt - 1) * NETWORK_WAIT_SECONDS} 秒）")
            return True
        if attempt == 1:
            log("网络尚未就绪，等待重试…")
        else:
            log(f"网络仍不可用，继续等待（第 {attempt}/{NETWORK_WAIT_ATTEMPTS} 次）")
        time.sleep(NETWORK_WAIT_SECONDS)
    log("网络始终不可用，本次跳过")
    return False


def fetch_bvids(mid):
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True}
    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE
    url = f"https://space.bilibili.com/{mid}/upload/video"
    last = None
    for attempt in range(1, 4):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            return [e["id"] for e in (info.get("entries") or []) if e and e.get("id")]
        except Exception as e:
            last = e
            log(f"拉取投稿列表失败：{e}")
            if attempt < 3 and not wait_for_network():
                break
    raise last


def fetch_meta(client, bv):
    err = None
    for attempt in range(4):
        try:
            d = client.get("https://api.bilibili.com/x/web-interface/view",
                           params={"bvid": bv}).json()
            if d.get("code") == 0:
                return d["data"]
            err = f"code={d.get('code')} {d.get('message', '')}"
        except Exception as e:
            err = str(e)
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(err)


def restriction(meta):
    if meta.get("is_upower_exclusive"):
        return "upower"
    rights = meta.get("rights") or {}
    if rights.get("pay") or rights.get("arc_pay") or rights.get("ugc_pay"):
        return "paid"
    return None


def norm_title(s):
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", s or "").lower()


MEDIA_EXTS = {".mp4", ".mkv", ".webm", ".flv", ".m4a", ".mp3"}


def build_existing_index(out_dir):
    idx = {}
    if not os.path.isdir(out_dir):
        return idx
    for name in os.listdir(out_dir):
        path = os.path.join(out_dir, name)
        if not os.path.isfile(path) or name.startswith("."):
            continue
        if os.path.splitext(name)[1].lower() not in MEDIA_EXTS:
            continue  # 排除 .part/.ytdl 等未完成文件
        idx[norm_title(os.path.splitext(name)[0])] = path
    return idx


def find_existing(title, idx):
    keys = []
    for cand in (title, sanitize_filename(title)):
        k = norm_title(cand)
        if k and k not in keys:
            keys.append(k)
    for k in keys:
        if k in idx:
            return idx[k]
    # 长标题可能被文件系统截断，只在唯一命中时采用前缀匹配
    for k in keys:
        if len(k) < 20:
            continue
        hits = [p for stem, p in idx.items()
                if stem.startswith(k[:20]) or k.startswith(stem[:20])]
        if len(hits) == 1:
            return hits[0]
    return None


def find_ffmpeg_dir():
    from downloader import _find_ffmpeg_path
    return _find_ffmpeg_path()


def check_space(out_dir, min_free_gb=2):
    free = shutil.disk_usage(out_dir).free
    if free < min_free_gb * 1024 ** 3:
        raise RuntimeError(f"磁盘剩余空间不足 {min_free_gb}GB（当前 {free / 1024 ** 3:.1f}GB）")


def download_one(bv, out_dir):
    opts = {
        "format": "bestvideo+bestaudio/best",
        "format_sort": ["vcodec:h264"],
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
    }
    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE
    ffmpeg_dir = find_ffmpeg_dir()
    if ffmpeg_dir:
        opts["ffmpeg_location"] = ffmpeg_dir

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"https://www.bilibili.com/video/{bv}/", download=True)
        rd = (info.get("requested_downloads") or [{}])[0]
        path = rd.get("filepath")
        if not path or not os.path.exists(path):
            candidate = ydl.prepare_filename(info)
            path = candidate if os.path.exists(candidate) else None
        if not path:
            stem = norm_title(info.get("title", ""))
            cands = [os.path.join(out_dir, f) for f in os.listdir(out_dir)
                     if norm_title(os.path.splitext(f)[0]) == stem]
            if cands:
                path = max(cands, key=os.path.getmtime)
        return path


def run_sync(args):
    lock = acquire_lock()  # noqa: F841 保持锁到进程结束
    threading.Thread(target=keep_awake_loop, daemon=True).start()
    os.makedirs(args.out, exist_ok=True)
    spath = state_path(args.mid)
    state = load_state(spath)
    videos = state.setdefault("videos", {})

    if not wait_for_network():
        return 1

    log(f"拉取 UP 主 {args.mid} 投稿列表…")
    try:
        bvids = fetch_bvids(args.mid)
    except Exception as e:
        log(f"获取投稿列表失败，本次放弃：{e}（明天会再试）")
        return 1
    if args.limit:
        bvids = bvids[:args.limit]
    log(f"共 {len(bvids)} 个投稿")

    existing = build_existing_index(args.out)
    stats = Counter()
    headers = {"User-Agent": UA, "Referer": "https://space.bilibili.com/"}
    with httpx.Client(timeout=20, headers=headers, cookies=buvid_cookies(),
                      follow_redirects=True) as client:
        for i, bv in enumerate(bvids, 1):
            rec = videos.get(bv) or {}
            if rec.get("status") in ("downloaded", "deleted"):
                # 已归档过的视频以状态文件为准；用户看完后手动删文件也不再重新下载
                if rec["status"] == "downloaded" and rec.get("path") and not os.path.exists(rec["path"]):
                    rec["status"] = "deleted"
                    rec["deleted_at"] = now()
                stats["already"] += 1
                continue
            if rec.get("status") == "skipped":
                stats["skipped"] += 1
                continue

            try:
                meta = fetch_meta(client, bv)
            except Exception as e:
                log(f"[{i}/{len(bvids)}] {bv} 获取信息失败：{e}")
                videos[bv] = {"status": "failed", "error": str(e), "at": now()}
                save_state(spath, state)
                stats["failed"] += 1
                continue

            title = meta.get("title") or bv
            reason = restriction(meta)
            if reason:
                label = "充电专属" if reason == "upower" else "付费"
                videos[bv] = {"status": "skipped", "reason": reason, "title": title, "at": now()}
                save_state(spath, state)
                stats["skipped"] += 1
                log(f"[{i}/{len(bvids)}] 跳过{label}：{title}")
                continue

            hit = find_existing(title, existing)
            if hit:
                videos[bv] = {"status": "downloaded", "title": title, "path": hit,
                              "source": "existing", "at": now()}
                save_state(spath, state)
                stats["existing"] += 1
                log(f"[{i}/{len(bvids)}] 已存在：{os.path.basename(hit)}")
                continue

            if args.dry_run:
                stats["pending"] += 1
                log(f"[{i}/{len(bvids)}] 待下载：{title}")
                continue

            try:
                check_space(args.out)
                log(f"[{i}/{len(bvids)}] 下载：{title}")
                path = download_one(bv, args.out)
                videos[bv] = {"status": "downloaded", "title": title, "path": path or "",
                              "duration": meta.get("duration"), "at": now()}
                stats["downloaded"] += 1
                if path:
                    existing[norm_title(title)] = path
                log(f"    完成：{os.path.basename(path) if path else '(未找到输出文件)'}")
            except Exception as e:
                videos[bv] = {"status": "failed", "title": title, "error": str(e), "at": now()}
                stats["failed"] += 1
                log(f"    失败：{e}")
            save_state(spath, state)
            time.sleep(2)

    state["last_run"] = now()
    save_state(spath, state)
    log(f"完成：新下载 {stats['downloaded']}，已存在 {stats['existing']}，"
        f"此前已下载 {stats['already']}，跳过 {stats['skipped']}，"
        f"失败 {stats['failed']}，待下载 {stats['pending']}")
    return 0


def parse_time(value):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", value.strip())
    if not m:
        raise SystemExit("时间格式应为 HH:MM，例如 09:00")
    hour, minute = int(m.group(1)), int(m.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise SystemExit("时间超出范围")
    return hour, minute


def parse_schedule(value, every_hours=None):
    hour, minute = parse_time(value)
    if not every_hours:
        return [(hour, minute)]
    if not (1 <= every_hours <= 24) or 24 % every_hours:
        raise SystemExit("--every-hours 必须是能整除 24 的整数（1/2/3/4/6/8/12/24）")
    return sorted(((hour + i * every_hours) % 24, minute)
                  for i in range(24 // every_hours))


def install_schedule(value, args):
    times = parse_schedule(value, args.every_hours)
    os.makedirs(os.path.dirname(PLIST_PATH), exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    triggers = "".join(
        f"    <dict><key>Hour</key><integer>{hour}</integer>"
        f"<key>Minute</key><integer>{minute}</integer></dict>\n"
        for hour, minute in times
    )
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{PLIST_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{sys.executable}</string>
    <string>{os.path.abspath(__file__)}</string>
    <string>--check</string>
    <string>--mid</string><string>{args.mid}</string>
    <string>--out</string><string>{args.out}</string>
  </array>
  <key>WorkingDirectory</key><string>{BACKEND_DIR}</string>
  <key>StartCalendarInterval</key>
  <array>
{triggers}  </array>
  <key>StandardOutPath</key><string>{os.path.join(DATA_DIR, "bili_sync.out.log")}</string>
  <key>StandardErrorPath</key><string>{os.path.join(DATA_DIR, "bili_sync.err.log")}</string>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
"""
    with open(PLIST_PATH, "w", encoding="utf-8") as f:
        f.write(plist)
    uid = os.getuid()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}", PLIST_PATH],
                   capture_output=True, check=False)
    subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", PLIST_PATH], check=True)
    log("已安装定时任务：" + "、".join(f"{h:02d}:{m:02d}" for h, m in times))
    log(f"修改时间：重新执行 --install-schedule HH:MM [--every-hours N] 即可（{PLIST_PATH}）")
    log(f"输出目录：{args.out}，日志：{os.path.join(DATA_DIR, 'bili_sync.out.log')}")
    return 0


def uninstall_schedule():
    uid = os.getuid()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}", PLIST_PATH],
                   capture_output=True, check=False)
    if os.path.exists(PLIST_PATH):
        os.remove(PLIST_PATH)
    log("已卸载定时任务")
    return 0


def main():
    parser = argparse.ArgumentParser(description="B站 UP 主视频同步（跳过充电视频）")
    parser.add_argument("--sync", action="store_true", help="补下载所有未下载的非充电视频")
    parser.add_argument("--check", action="store_true", help="检查并下载新视频")
    parser.add_argument("--dry-run", action="store_true", help="只列出将要下载的视频")
    parser.add_argument("--mid", default=DEFAULT_MID, help="UP 主 UID")
    parser.add_argument("--out", default=DEFAULT_OUT_DIR, help="下载目录")
    parser.add_argument("--limit", type=int, help="只处理列表前 N 个（调试用）")
    parser.add_argument("--install-schedule", metavar="HH:MM", help="安装定时任务（配合 --every-hours 可多次）")
    parser.add_argument("--every-hours", type=int, metavar="N",
                        help="从 --install-schedule 的时间起每 N 小时运行一次（需整除 24）")
    parser.add_argument("--uninstall-schedule", action="store_true", help="卸载定时任务")
    args = parser.parse_args()

    if args.install_schedule:
        return install_schedule(args.install_schedule, args)
    if args.uninstall_schedule:
        return uninstall_schedule()
    if args.sync or args.check:
        return run_sync(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
