# B 站 UP 主自动归档指南（bili_sync.py）

`bili_sync.py` 用于把指定 UP 主的**免费视频**自动归档到本地，并每天定时检查新投稿。充电专属/付费视频只记录、不下载，不做任何绕过。

- UP 主 UID：`351413419`（野生量化员）
- 下载目录：`/Users/shadow/Downloads/野生量化员`
- 定时时间：每天 `00:00`、`02:00` … `22:00`，每 2 小时一次，共 12 次
- 不依赖本项目后端（FastAPI）是否启动，独立运行

---

## 1. 文件与路径

| 用途 | 路径 |
| --- | --- |
| 主脚本 | `backend/bili_sync.py` |
| 归档状态（权威记录） | `backend/data/bili_sync_351413419.json` |
| 运行锁 | `backend/data/bili_sync.lock` |
| 定时任务日志 | `backend/data/bili_sync.out.log` / `bili_sync.err.log` |
| launchd 配置 | `~/Library/LaunchAgents/com.wildquant.bili-sync.plist` |
| B 站 Cookie（可选） | `backend/bilibili_cookies.txt` |
| 下载目录 | `/Users/shadow/Downloads/野生量化员` |

依赖：`backend/.venv` 中的 Python 3.13、`yt-dlp`、`httpx`；ffmpeg 由 `downloader._find_ffmpeg_path()` 查找。launchd 环境的 PATH 只有 `/usr/bin:/bin`，所以该函数在 `shutil.which` 失败后会显式探测 `/opt/homebrew/bin`、`/usr/local/bin`、`/usr/bin`、`/bin`（当前命中 `/opt/homebrew/bin`），最后才回退 `static_ffmpeg`。

---

## 2. 日常运行：不需要手动执行

launchd 会在每天 `00:00`、`02:00` … `22:00`（每 2 小时）自动调用：

```bash
backend/.venv/bin/python backend/bili_sync.py --check \
  --mid 351413419 --out /Users/shadow/Downloads/野生量化员
```

### 重启 / 睡眠 / 关机时的行为

- **重启**：`~/Library/LaunchAgents` 下的任务在用户登录桌面后自动加载，不需要重新安装。若停在登录界面未登录，任务不会运行。
- **睡眠**：到点时系统在睡眠，任务会在唤醒后补跑。
- **关机**：错过的时间点不会立即执行；但下一次运行会扫描完整投稿列表，把没归档过的视频全部补上。
- **项目目录或 `.venv` 被移动**：plist 里是绝对路径，需要重新执行一次安装命令。

### 修改时间 / 卸载

```bash
cd backend
.venv/bin/python bili_sync.py --install-schedule 08:00 --every-hours 2  # 从 08:00 起每 2 小时一次（当前配置）
.venv/bin/python bili_sync.py --install-schedule 08:00                  # 只保留每天一次
.venv/bin/python bili_sync.py --uninstall-schedule                       # 卸载
```

`--every-hours N` 要求 N 能整除 24（1/2/3/4/6/8/12/24），跨午夜自动环绕，例如 `08:00` + `2` 会生成 `00:00、02:00 … 22:00`。

安装命令会重写 plist 并执行 `launchctl bootout` + `bootstrap`，立即生效。

---

## 3. 手动命令

```bash
cd backend

# 补下载所有没归档过的免费视频（也可用 --check，两者行为一致）
.venv/bin/python bili_sync.py --sync

# 只列出会下载什么，不实际下载
.venv/bin/python bili_sync.py --sync --dry-run

# 只处理列表前 N 个（调试用）
.venv/bin/python bili_sync.py --sync --limit 5

# 临时换 UP 主 / 下载目录
.venv/bin/python bili_sync.py --sync --mid 123456 --out /path/to/dir
```

查看进度：

```bash
cd backend
.venv/bin/python - <<'PY'
import json, collections
s = json.load(open("data/bili_sync_351413419.json"))
print(dict(collections.Counter(v.get("status") for v in s["videos"].values())))
print("last_run:", s.get("last_run"))
PY
```

或直接看日志尾部：

```bash
tail -f backend/data/bili_sync.out.log
```

---

## 4. 状态文件规则（最重要）

状态文件按 BV 号记录每个视频，例如：

```json
"BV1HenY6DEyR": {
  "status": "downloaded",
  "title": "美债超40万亿美元……",
  "path": "/Users/shadow/Downloads/野生量化员/…….mp4",
  "at": "2026-10-24 10:42:47"
}
```

| status | 含义 | 下次运行 |
| --- | --- | --- |
| `downloaded` | 已归档 | 跳过 |
| `deleted` | 曾归档，文件已被手动删除 | 跳过（**不会重新下载**） |
| `skipped` | 充电专属/付费，不下载 | 跳过 |
| `failed` | 获取信息或下载失败 | 重试 |

规则：

1. **状态文件是权威依据**。只要记录过 `downloaded` / `skipped` / `deleted`，就永久跳过，不再看文件是否存在。看完视频后删掉文件，不会被重新下载。
2. 每次运行仍会扫描**完整投稿列表**，但只处理状态文件里没有的视频，以及 `failed` 的视频。这是补齐漏跑那几天的前提。
3. 每个视频处理完立即落盘；中断后重跑会从断点继续。
4. 同一时间只允许一个实例运行（`flock` 锁），定时任务撞上手动任务时会直接退出。

### 重新下载某个视频

先停掉正在运行的任务，删除该 BV 号对应的记录，再执行 `--sync`：

```bash
cd backend
.venv/bin/python - <<'PY'
import json
p = "data/bili_sync_351413419.json"
s = json.load(open(p))
s["videos"].pop("BV号", None)
json.dump(s, open(p, "w"), ensure_ascii=False, indent=1)
PY
.venv/bin/python bili_sync.py --sync
```

> 任务运行时不要手改状态文件，进程会用内存里的副本覆盖它。

---

## 5. 下载行为与限制

- **免费/付费判断**：调用 `x/web-interface/view`，`is_upower_exclusive` 或 `rights` 中的付费标记为 `skipped`，不进入下载。
- **画质**：当前 Cookie 无有效登录态，B 站只给到 480p。这是账号限制，不是脚本 bug。
- **编码**：B 站同分辨率优先选 H.264（`format_sort: ["vcodec:h264"]`），合并为 mp4，兼容 QuickTime。
- **命名**：使用视频标题，自动清理文件系统非法字符。
- **已有文件匹配**：按“标题归一化”匹配下载目录里的成品文件，避免重复下载；只认 `.mp4/.mkv/.webm/.flv/.m4a/.mp3`，**`.part` 等未完成文件不参与匹配**。
- **网络**：`socket_timeout=30`，下载/分片各重试 10 次；中断的分片会在下次运行时续传。启动时会先探测 `api.bilibili.com` 是否可达，未就绪则每 20 秒重试，最多 6 次（约 100 秒，参数 `NETWORK_WAIT_ATTEMPTS` / `NETWORK_WAIT_SECONDS`），日志打印“网络尚未就绪，等待重试…”；等不到就退出，交给 2 小时后的下一次触发，避免长进程占着运行锁把后续触发点挤掉。拉取投稿列表失败会再整体重试 3 轮。
- **磁盘**：每次下载前检查剩余空间，低于 2GB 时该视频记失败并继续下一个。
- **电源策略**：运行期间每 30 秒检查一次电源，**插电或电池 >30%** 时阻止空闲睡眠；低于 30% 且未插电时允许系统休眠（任务暂停，唤醒后续传）。阈值和间隔在脚本顶部（`BATTERY_FLOOR_PCT`）。
- **Cookie**：文件存在时传给 yt-dlp，并取出 `buvid3` / `b_nut` 用于元数据请求；不存在也能运行。

---

## 6. 常见问题

**任务没跑**
```bash
launchctl print gui/$(id -u)/com.wildquant.bili-sync | grep -E "state|runs|last exit"
tail -20 backend/data/bili_sync.err.log
```
确认 plist 存在、用户已登录桌面会话、`.venv/bin/python` 路径仍然有效。

**手动触发一次定时任务**
```bash
launchctl kickstart -k gui/$(id -u)/com.wildquant.bili-sync
```

**下载很慢或停住**
macOS 空闲睡眠会暂停进程。脚本已内置电源策略：插电或电池 >30% 时自动阻止空闲睡眠，日志里会打印“下载期间阻止系统睡眠（…）”；掉到 30% 以下且未插电时允许休眠。若日志显示已允许睡眠，插电即可恢复全速，无需再手动套 `caffeinate`。

合盖（clamshell）时系统仍会休眠，任何断言都无效，唤醒后自动续传。

**任务启动了但日志只有“拉取投稿列表”而失败**
原因是系统处在暗唤醒（DarkWake）：Wi-Fi/DNS 还没起来，首个请求就解析失败（`Failed to resolve 'api.bilibili.com'`）。脚本会先等网络约 100 秒，等不到就退出，2 小时后的下一次触发会再试；`pmset -g log | grep -i darkwake` 可核实唤醒原因。若当天仍没下载，手动 kickstart 一次即可补齐。

**目录里残留 `.part`**
未完成的视频分片，正常现象；下次运行会续传，且不会被误判为已完成。确认没有下载任务后可以手动删除。

**磁盘空间不足**
日志会出现“磁盘剩余空间不足 2GB”；清理空间后重新 `--sync`，失败项会自动重试。

**日志越来越大**
日志只追加不轮转，可定期清空：
```bash
: > backend/data/bili_sync.out.log
: > backend/data/bili_sync.err.log
```

---

## 7. 边界

- 只归档**不需要充电/付费权限**的视频；会员到期或无有效登录态时，能拿到的最高画质就是 480p。
- 任何“下载会员/充电专属视频”的需求，都需要有效账号权限，脚本不提供绕过方案。
