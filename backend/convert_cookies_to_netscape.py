#!/usr/bin/env python3
"""
将JSON格式的Cookie文件转换为Netscape格式
"""

import json
import os
from datetime import datetime, timezone, timedelta

def json_to_netscape(json_cookies):
    """将JSON格式的Cookie转换为Netscape格式"""
    netscape_cookies = []
    
    for cookie in json_cookies:
        # 转换过期时间
        expires = cookie.get('expires', 0)
        if expires == 0:
            # 如果没有过期时间，设置为一年后
            future_time = datetime.now(timezone.utc) + timedelta(days=365)
            expires = int(future_time.timestamp())
        elif isinstance(expires, str):
            # 如果是字符串格式的时间戳，转换为整数
            try:
                expires = int(expires)
            except ValueError:
                # 如果无法转换，设置为一年后
                future_time = datetime.now(timezone.utc) + timedelta(days=365)
                expires = int(future_time.timestamp())
        
        # 创建Netscape格式的Cookie行
        netscape_cookie = (
            f"{cookie.get('domain', '')}\t"
            f"{'TRUE' if cookie.get('domain', '').startswith('.') else 'FALSE'}\t"
            f"{cookie.get('path', '/')}\t"
            f"{'TRUE' if cookie.get('secure', False) else 'FALSE'}\t"
            f"{expires}\t"
            f"{cookie.get('name', '')}\t"
            f"{cookie.get('value', '')}"
        )
        
        netscape_cookies.append(netscape_cookie)
    
    return netscape_cookies

def convert_cookies_file():
    """转换Cookie文件格式"""
    json_file = "bilibili_cookies.txt"
    netscape_file = "bilibili_cookies_netscape.txt"
    
    if not os.path.exists(json_file):
        print(f"❌ JSON Cookie文件不存在: {json_file}")
        return
    
    try:
        # 读取JSON格式的Cookie
        with open(json_file, 'r', encoding='utf-8') as f:
            json_cookies = json.load(f)
        
        print(f"✅ 读取到 {len(json_cookies)} 个JSON格式Cookie")
        
        # 转换为Netscape格式
        netscape_cookies = json_to_netscape(json_cookies)
        print(f"✅ 转换为 {len(netscape_cookies)} 个Netscape格式Cookie")
        
        # 保存为Netscape格式
        with open(netscape_file, 'w', encoding='utf-8') as f:
            # 写入文件头注释
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# https://curl.se/docs/http-cookies.html\n")
            f.write("# This file was converted from JSON format\n\n")
            
            # 写入Cookie行
            for cookie in netscape_cookies:
                f.write(cookie + "\n")
        
        print(f"✅ Cookie已保存为Netscape格式: {netscape_file}")
        
        # 显示主要Cookie
        print("\n主要Cookie:")
        important_cookies = ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'sid']
        for cookie in netscape_cookies:
            parts = cookie.split('\t')
            if len(parts) >= 7 and parts[5] in important_cookies:
                name = parts[5]
                value = parts[6]
                print(f"  {name}: {value[:20]}...")
        
        return netscape_file
        
    except Exception as e:
        print(f"❌ 转换失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=== JSON to Netscape Cookie Converter ===")
    
    netscape_file = convert_cookies_file()
    
    if netscape_file:
        print(f"\n🎉 转换完成!")
        print(f"请使用以下文件作为yt-dlp的Cookie文件:")
        print(f"  {os.path.abspath(netscape_file)}")
        print(f"\n在代码中，将cookies参数指向这个文件:")
        print(f"  downloader.parse_video(url, '{netscape_file}')")