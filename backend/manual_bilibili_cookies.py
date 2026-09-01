#!/usr/bin/env python3
"""
手动创建B站Cookie文件
从浏览器开发者工具中复制Cookie值
"""

import os
import json

COOKIES_FILE = "bilibili_cookies.txt"

def create_netscape_cookie_file(sessdata, bili_jct, dede_user_id, dede_user_id_ckmd5="", sid=""):
    """创建Netscape格式的Cookie文件"""
    
    # 计算过期时间：1年后
    import time
    expires = int(time.time()) + 365 * 24 * 3600
    
    lines = [
        "# Netscape HTTP Cookie File",
        "# https://curl.se/docs/http-cookies.html",
        "# This is a generated file!  Do not edit.",
        "",
    ]
    
    cookies = [
        (".bilibili.com", "TRUE", "/", "TRUE", expires, "SESSDATA", sessdata),
        (".bilibili.com", "TRUE", "/", "TRUE", expires, "bili_jct", bili_jct),
        (".bilibili.com", "TRUE", "/", "TRUE", expires, "DedeUserID", dede_user_id),
    ]
    
    if dede_user_id_ckmd5:
        cookies.append((".bilibili.com", "TRUE", "/", "TRUE", expires, "DedeUserID__ckMd5", dede_user_id_ckmd5))
    
    if sid:
        cookies.append((".bilibili.com", "TRUE", "/", "FALSE", expires, "sid", sid))
    
    for domain, subdomain, path, secure, expire, name, value in cookies:
        lines.append(f"{domain}\t{subdomain}\t{path}\t{secure}\t{expire}\t{name}\t{value}")
    
    with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    
    return COOKIES_FILE


def main():
    print("=" * 60)
    print("  B站Cookie手动创建工具")
    print("=" * 60)
    print()
    print("请按以下步骤从Chrome浏览器中获取Cookie值：")
    print()
    print("1. 打开Chrome浏览器，访问 https://www.bilibili.com 并登录")
    print("2. 按 F12 打开开发者工具")
    print("3. 点击顶部 'Application' (应用程序) 标签")
    print("4. 左侧展开 'Storage' > 'Cookies' > 'https://www.bilibili.com'")
    print("5. 在右侧列表中找到以下Cookie，复制它们的值：")
    print()
    print("   必需的Cookie：")
    print("   ┌─────────────────┬────────────────────────────────────────┐")
    print("   │ 名称            │ 说明                                   │")
    print("   ├─────────────────┼────────────────────────────────────────┤")
    print("   │ SESSDATA        │ 会话ID（最重要的！很长的一串字符）       │")
    print("   │ bili_jct        │ CSRF令牌（32位十六进制字符串）           │")
    print("   │ DedeUserID      │ 你的B站用户ID（纯数字）                 │")
    print("   └─────────────────┴────────────────────────────────────────┘")
    print()
    print("   可选的Cookie：")
    print("   ┌─────────────────┬────────────────────────────────────────┐")
    print("   │ DedeUserID__ckMd5│ 用户ID的MD5哈希                       │")
    print("   │ sid             │ 会话ID                                  │")
    print("   └─────────────────┴────────────────────────────────────────┘")
    print()
    print("提示：在Cookie列表中点击名称列可以按名称排序，方便查找")
    print()
    
    # 获取Cookie值
    sessdata = input("请输入 SESSDATA 的值: ").strip()
    if not sessdata:
        print("❌ SESSDATA 是必需的！")
        return
    
    bili_jct = input("请输入 bili_jct 的值: ").strip()
    if not bili_jct:
        print("❌ bili_jct 是必需的！")
        return
    
    dede_user_id = input("请输入 DedeUserID 的值: ").strip()
    if not dede_user_id:
        print("❌ DedeUserID 是必需的！")
        return
    
    dede_user_id_ckmd5 = input("请输入 DedeUserID__ckMd5 的值（可选，直接回车跳过）: ").strip()
    sid = input("请输入 sid 的值（可选，直接回车跳过）: ").strip()
    
    # 创建Cookie文件
    print()
    print("正在创建Cookie文件...")
    cookie_file = create_netscape_cookie_file(
        sessdata=sessdata,
        bili_jct=bili_jct,
        dede_user_id=dede_user_id,
        dede_user_id_ckmd5=dede_user_id_ckmd5,
        sid=sid,
    )
    
    print(f"✅ Cookie文件已创建: {os.path.abspath(cookie_file)}")
    print()
    print("现在你可以使用以下命令下载B站视频：")
    print("  cd backend")
    print("  python test_bilibili_download.py")
    print()
    print("或者在Python代码中使用：")
    print("  from downloader import VideoDownloader")
    print("  downloader = VideoDownloader()")
    print("  downloader.download_video(url, 'best', 'bilibili_cookies.txt')")


if __name__ == "__main__":
    main()
