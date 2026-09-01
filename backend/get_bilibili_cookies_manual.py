#!/usr/bin/env python3
"""
B站 Cookie 手动配置工具（无需钥匙串权限）

这个工具完全不依赖钥匙串访问，通过以下方式获取 Cookie：
1. 从 Safari 浏览器获取（如果 Safari 也登录了 B站）
2. 引导您从 Chrome 开发工具手动复制 Cookie
3. 使用浏览器扩展导出的 cookies.txt 文件

使用方法:
    cd backend
    python get_bilibili_cookies_manual.py
"""

import os
import sys
from pathlib import Path


TARGET_FILE = os.path.join(os.path.dirname(__file__), "bilibili_cookies.txt")


def print_header():
    print("=" * 60)
    print("B站 Cookie 配置工具（手动版）")
    print("=" * 60)
    print("这个工具不需要钥匙串权限，通过多种方式配置 Cookie")
    print()


def try_safari_cookies():
    """尝试从 Safari 获取 Cookie（无需钥匙串）"""
    print("\n=== 方法 1: 从 Safari 浏览器获取 ===")
    print("如果您在 Safari 中也登录了 B站，可以尝试此方法")
    
    try:
        import yt_dlp
        import yt_dlp.cookies
        
        choice = input("是否尝试从 Safari 读取 Cookie？(y/N): ").strip().lower()
        if choice != 'y':
            return None
        
        print("正在尝试从 Safari 浏览器读取 Cookie...")
        jar = yt_dlp.cookies.extract_cookies_from_browser('safari', None, yt_dlp.cookies.YDLLogger())
        
        # 检查是否有 SESSDATA
        names = [c.name for c in jar if c.value]
        if 'SESSDATA' in names:
            sessdata = next(c for c in jar if c.name == 'SESSDATA')
            print(f"✅ 成功从 Safari 获取 {len(jar)} 个 Cookie")
            print(f"SESSDATA: {sessdata.value[:20]}...")
            
            # 转换为字典格式
            cookies = []
            for c in jar:
                if 'bilibili.com' in c.domain:
                    cookies.append({
                        'name': c.name,
                        'value': c.value,
                        'domain': c.domain,
                        'path': c.path,
                        'expires': c.expires or 0,
                        'secure': c.secure,
                        'httponly': c._rest.get('HttpOnly', False)
                    })
            return cookies
        else:
            print("❌ Safari 中未找到有效的 B站 Cookie")
            return None
    except Exception as e:
        print(f"❌ Safari 读取失败: {str(e)}")
        return None


def import_cookies_file():
    """导入 cookies.txt 文件"""
    print("\n=== 方法 2: 导入 cookies.txt 文件 ===")
    print("如果您已通过浏览器扩展导出 cookies.txt 文件，使用此方法")
    
    choice = input("是否已导出 cookies.txt 文件？(y/N): ").strip().lower()
    if choice != 'y':
        return None
    
    file_path = input("请输入 cookies.txt 文件路径（或拖拽文件到终端）: ").strip()
    file_path = os.path.expanduser(file_path)
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return None
    
    # 验证文件格式
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if 'SESSDATA' not in content:
                print("❌ 文件中未找到 SESSDATA")
                return None
            
            # 检查是否有非空 SESSDATA
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    parts = line.split('\t')
                    if len(parts) >= 7 and parts[5] == 'SESSDATA' and parts[6].strip():
                        print(f"✅ 文件验证成功，找到有效的 SESSDATA")
                        return file_path
            
            print("❌ 文件中 SESSDATA 为空")
            return None
    except Exception as e:
        print(f"❌ 文件读取失败: {str(e)}")
        return None


def manual_copy_cookies():
    """手动复制 Cookie 值"""
    print("\n=== 方法 3: 手动复制 Cookie 值 ===")
    print("请在 Chrome 中按以下步骤操作：")
    print("1. 访问 https://www.bilibili.com 并登录")
    print("2. 按 F12 打开开发者工具")
    print("3. 点击 Application 标签")
    print("4. 左侧展开 Storage → Cookies → https://www.bilibili.com")
    print("5. 在右侧找到并复制以下 Cookie 的值：\n")
    
    # 检查是否在交互环境
    if not sys.stdin.isatty():
        print("⚠️ 当前不是交互式终端")
        print("请在您的终端中运行此脚本")
        return None
    
    print("\n请输入以下 Cookie 值（必需项不能为空）：\n")
    
    sessdata = input("SESSDATA (必需): ").strip()
    if not sessdata:
        print("❌ SESSDATA 不能为空")
        return None
    
    bili_jct = input("bili_jct (必需): ").strip()
    if not bili_jct:
        print("❌ bili_jct 不能为空")
        return None
    
    dedeuserid = input("DedeUserID (必需): ").strip()
    if not dedeuserid:
        print("❌ DedeUserID 不能为空")
        return None
    
    # 可选项
    print("\n可选 Cookie（直接回车跳过）：")
    dedeuserid_ckmd5 = input("DedeUserID__ckMd5: ").strip()
    sid = input("sid: ").strip()
    buvid3 = input("buvid3: ").strip()
    
    cookies = [
        {
            'name': 'SESSDATA',
            'value': sessdata,
            'domain': '.bilibili.com',
            'path': '/',
            'secure': True,
            'httponly': True
        },
        {
            'name': 'bili_jct',
            'value': bili_jct,
            'domain': '.bilibili.com',
            'path': '/',
            'secure': True,
            'httponly': False
        },
        {
            'name': 'DedeUserID',
            'value': dedeuserid,
            'domain': '.bilibili.com',
            'path': '/',
            'secure': True,
            'httponly': False
        }
    ]
    
    if dedeuserid_ckmd5:
        cookies.append({
            'name': 'DedeUserID__ckMd5',
            'value': dedeuserid_ckmd5,
            'domain': '.bilibili.com',
            'path': '/',
            'secure': True,
            'httponly': False
        })
    
    if sid:
        cookies.append({
            'name': 'sid',
            'value': sid,
            'domain': '.bilibili.com',
            'path': '/',
            'secure': False,
            'httponly': False
        })
    
    if buvid3:
        cookies.append({
            'name': 'buvid3',
            'value': buvid3,
            'domain': '.bilibili.com',
            'path': '/',
            'secure': False,
            'httponly': False
        })
    
    return cookies


def save_cookies_to_netscape(cookies_or_file):
    """保存 Cookie 到 Netscape 格式文件"""
    try:
        lines = [
            "# Netscape HTTP Cookie File",
            "# Generated by get_bilibili_cookies_manual.py"
        ]
        
        expiry = 1900000000  # 2030年左右
        
        if isinstance(cookies_or_file, str):
            # 是文件路径，直接复制
            import shutil
            shutil.copy2(cookies_or_file, TARGET_FILE)
        else:
            # 是 Cookie 列表
            for cookie in cookies_or_file:
                secure = "TRUE" if cookie.get('secure', False) else "FALSE"
                lines.append(
                    f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{secure}\t{expiry}\t{cookie['name']}\t{cookie['value']}"
                )
            
            with open(TARGET_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
        
        print(f"\n✅ Cookie 文件已保存到: {TARGET_FILE}")
        return True
    except Exception as e:
        print(f"❌ 保存失败: {str(e)}")
        return False


def validate_cookies():
    """验证 Cookie 文件是否有效"""
    if not os.path.exists(TARGET_FILE):
        return False
    
    try:
        with open(TARGET_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.rstrip('\n').rstrip('\r')
                if not line or line.startswith('#') or line.lower().startswith('format'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 7 and parts[5] == 'SESSDATA' and parts[6].strip():
                    return True
        return False
    except:
        return False


def test_cookies():
    """测试 Cookie"""
    print("\n=== 测试 Cookie ===")
    
    test_url = input("输入一个 B站会员视频 URL 进行测试（留空跳过）: ").strip()
    if not test_url:
        print("跳过测试")
        return
    
    try:
        from downloader import VideoDownloader
        downloader = VideoDownloader()
        
        print(f"正在解析: {test_url}")
        info = downloader.parse_video(test_url)
        
        print(f"✅ 解析成功！")
        print(f"标题: {info['title']}")
        print(f"时长: {info['duration_string']}")
        print(f"可用格式: {len(info['formats'])}个")
        
        # 显示前3个格式
        print("\n前 3 个格式:")
        for i, fmt in enumerate(info['formats'][:3], 1):
            print(f"  {i}. {fmt['label']}")
        
        print("\n✅ Cookie 测试通过！")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        print("可能原因：")
        print("  1. Cookie 已过期")
        print("  2. 账号没有该视频的观看权限")
        print("  3. 视频链接错误")


def main():
    print_header()
    
    # 检查现有 Cookie 文件
    if os.path.exists(TARGET_FILE) and validate_cookies():
        print(f"✅ 现有 Cookie 文件有效: {TARGET_FILE}")
        choice = input("是否重新配置？(y/N): ").strip().lower()
        if choice != 'y':
            print("使用现有 Cookie")
            test_cookies()
            return
    
    cookies_or_file = None
    
    # 方法 1: Safari
    cookies_or_file = try_safari_cookies()
    
    if not cookies_or_file:
        # 方法 2: 导入文件
        cookies_or_file = import_cookies_file()
    
    if not cookies_or_file:
        # 方法 3: 手动输入
        cookies_or_file = manual_copy_cookies()
    
    if not cookies_or_file:
        print("\n❌ 未获取到有效的 Cookie")
        return
    
    # 保存 Cookie
    if save_cookies_to_netscape(cookies_or_file):
        print("\n✅ 配置完成！")
        print("\n使用说明：")
        print("1. 重启后端: cd backend && python main.py")
        print("2. 访问 Web 界面: http://localhost:5173")
        print("3. 输入 B站会员视频 URL 即可下载")
        
        test_cookies()
    else:
        print("\n❌ 保存失败，请检查文件权限")


if __name__ == "__main__":
    main()