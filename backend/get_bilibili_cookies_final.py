#!/usr/bin/env python3
"""
一键获取 B站 Cookie 脚本

请在您的终端中运行此脚本（不要在 DSH 环境中运行），它会：
1. 尝试从 Chrome 浏览器自动提取 B站 Cookie
2. 如果失败，提供清晰的指导让您手动提供 Cookie
3. 自动保存到 backend/bilibili_cookies.txt

使用方法:
    cd backend
    python get_bilibili_cookies_final.py
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path


# 目标文件路径
TARGET_FILE = os.path.join(os.path.dirname(__file__), "bilibili_cookies.txt")


def check_environment():
    """检查运行环境"""
    print(f"当前用户: {os.getenv('USER', 'unknown')}")
    print(f"当前目录: {os.getcwd()}")
    print(f"Python 路径: {sys.executable}")
    print()


def try_browser_cookie3():
    """尝试使用 browser_cookie3 获取 Cookie"""
    print("=== 尝试方法 1: browser_cookie3 ===")
    try:
        import browser_cookie3
        print("browser_cookie3 已安装，正在尝试获取 Chrome Cookie...")
        
        cj = browser_cookie3.chrome(domain_name='bilibili.com')
        cookies = []
        
        for cookie in cj:
            if cookie.domain in [".bilibili.com", "www.bilibili.com", "bilibili.com"]:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'expires': cookie.expires,
                    'secure': cookie.secure,
                    'httponly': cookie.httponly
                })
        
        if cookies:
            sessdata = next((c for c in cookies if c['name'] == 'SESSDATA'), None)
            if sessdata and sessdata['value']:
                print(f"✅ 成功获取 {len(cookies)} 个 B站 Cookie")
                print(f"SESSDATA: {sessdata['value'][:20]}...")
                return cookies
            else:
                print("❌ 获取到 Cookie 但 SESSDATA 为空")
                return None
        else:
            print("❌ 未找到 B站 Cookie")
            return None
    except ImportError:
        print("❌ browser_cookie3 未安装")
        return None
    except Exception as e:
        print(f"❌ browser_cookie3 失败: {str(e)}")
        return None


def try_yt_dlp_browser():
    """尝试使用 yt-dlp 的 cookiesfrombrowser"""
    print("\n=== 尝试方法 2: yt-dlp cookiesfrombrowser ===")
    try:
        import yt_dlp
        import yt_dlp.cookies
        
        print("正在尝试从 Chrome 浏览器读取 Cookie...")
        
        jar = yt_dlp.cookies.extract_cookies_from_browser('chrome', None, yt_dlp.cookies.YDLLogger())
        names = [c.name for c in jar if c.value]
        
        if 'SESSDATA' in names:
            sessdata = next(c for c in jar if c.name == 'SESSDATA')
            print(f"✅ 成功获取 {len(jar)} 个 Cookie")
            print(f"SESSDATA: {sessdata.value[:20]}...")
            
            # 转换为我们的格式
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
            print("❌ 未找到 SESSDATA Cookie")
            return None
    except Exception as e:
        print(f"❌ yt-dlp cookiesfrombrowser 失败: {str(e)}")
        return None


def manual_input_method():
    """手动输入 Cookie 值"""
    print("\n=== 手动输入 Cookie ===")
    print("请在 Chrome 中按 F12 打开开发者工具")
    print("Application > Cookies > https://www.bilibili.com")
    print("复制以下 Cookie 的值：\n")
    
    # 检查是否在终端环境
    if not sys.stdin.isatty():
        print("⚠️ 当前不是交互式终端，无法直接输入")
        print("请在您的终端中运行：")
        print("  cd backend")
        print("  python get_bilibili_cookies_final.py")
        return None
    
    sessdata = input("SESSDATA (必需): ").strip()
    if not sessdata:
        print("❌ SESSDATA 不能为空")
        return None
    
    bili_jct = input("bili_jct (必需): ").strip()
    dedeuserid = input("DedeUserID (必需): ").strip()
    
    # 可选
    dedeuserid_ckmd5 = input("DedeUserID__ckMd5 (可选，直接回车跳过): ").strip()
    sid = input("sid (可选，直接回车跳过): ").strip()
    
    cookies = [
        {'name': 'SESSDATA', 'value': sessdata, 'domain': '.bilibili.com', 'path': '/', 'secure': True, 'httponly': True},
        {'name': 'bili_jct', 'value': bili_jct, 'domain': '.bilibili.com', 'path': '/', 'secure': True, 'httponly': False},
        {'name': 'DedeUserID', 'value': dedeuserid, 'domain': '.bilibili.com', 'path': '/', 'secure': True, 'httponly': False},
    ]
    
    if dedeuserid_ckmd5:
        cookies.append({'name': 'DedeUserID__ckMd5', 'value': dedeuserid_ckmd5, 'domain': '.bilibili.com', 'path': '/', 'secure': True, 'httponly': False})
    
    if sid:
        cookies.append({'name': 'sid', 'value': sid, 'domain': '.bilibili.com', 'path': '/', 'secure': False, 'httponly': False})
    
    print(f"✅ 已接收 {len(cookies)} 个 Cookie")
    return cookies


def write_netscape_file(cookies):
    """写入 Netscape 格式的 Cookie 文件"""
    if not cookies:
        return False
    
    lines = [
        "# Netscape HTTP Cookie File",
        "# Generated by get_bilibili_cookies_final.py",
    ]
    
    expiry = 1900000000  # 2030年左右
    
    for cookie in cookies:
        secure = "TRUE" if cookie.get('secure', False) else "FALSE"
        lines.append(f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{secure}\t{expiry}\t{cookie['name']}\t{cookie['value']}")
    
    try:
        with open(TARGET_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"\n✅ Cookie 文件已保存到: {TARGET_FILE}")
        return True
    except Exception as e:
        print(f"❌ 保存文件失败: {str(e)}")
        return False


def validate_cookie_file():
    """验证 Cookie 文件是否有效"""
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


def install_dependencies():
    """安装依赖"""
    print("\n=== 安装依赖 ===")
    deps = []
    
    try:
        import browser_cookie3
    except ImportError:
        deps.append('browser_cookie3')
    
    try:
        import yt_dlp
    except ImportError:
        deps.append('yt-dlp')
    
    if not deps:
        print("✅ 所有依赖已安装")
        return True
    
    print(f"需要安装: {', '.join(deps)}")
    choice = input("是否自动安装？(y/N): ").strip().lower()
    
    if choice == 'y':
        for dep in deps:
            print(f"安装 {dep}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
        print("✅ 依赖安装完成")
        return True
    
    print("跳过依赖安装")
    return False


def test_cookies():
    """测试 Cookie 是否有效"""
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
        print(f"平台: {info['platform']}")
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
    print("=" * 60)
    print("B站 Cookie 获取工具（一键配置）")
    print("=" * 60)
    print("此工具将在您的终端中运行，尝试从 Chrome 获取 B站 Cookie")
    print("请确保：")
    print("  1. Chrome 浏览器已打开并登录 B站")
    print("  2. 账号有会员权限")
    print("  3. 在您的终端中运行（不是在 DSH 环境中）")
    print()
    
    check_environment()
    
    # 检查现有文件
    if os.path.exists(TARGET_FILE):
        if validate_cookie_file():
            print(f"✅ 现有 Cookie 文件有效: {TARGET_FILE}")
            choice = input("是否重新配置？(y/N): ").strip().lower()
            if choice != 'y':
                print("使用现有 Cookie")
                test_cookies()
                return
        else:
            print(f"⚠️ 现有 Cookie 文件无效: {TARGET_FILE}")
    
    # 安装依赖
    if not install_dependencies():
        print("继续尝试其他方法...")
    
    cookies = None
    
    # 尝试方法 1: browser_cookie3
    cookies = try_browser_cookie3()
    
    if not cookies:
        # 尝试方法 2: yt-dlp
        cookies = try_yt_dlp_browser()
    
    if not cookies:
        # 手动输入
        cookies = manual_input_method()
    
    if not cookies:
        print("\n❌ 所有方法都失败了，无法获取 Cookie")
        print("请参考文档手动创建 Cookie 文件")
        return
    
    # 保存文件
    if write_netscape_file(cookies):
        print("\n✅ 配置完成！")
        print("\n后续步骤：")
        print("1. 重启后端服务: cd backend && python main.py")
        print("2. 访问 Web 界面: http://localhost:5173")
        print("3. 输入 B站会员视频 URL 即可下载")
        
        # 测试
        test_cookies()
    else:
        print("\n❌ 保存失败，请检查文件权限")


if __name__ == "__main__":
    main()