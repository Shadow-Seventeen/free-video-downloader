#!/usr/bin/env python3
import os
import json
import sqlite3
from browser_cookie3 import chrome

def get_chrome_cookies(domain):
    """获取Chrome浏览器中指定域名的cookie"""
    try:
        cj = chrome()
        cookies = []
        for cookie in cj:
            if cookie.domain == domain:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'expires': cookie.expires,
                    'secure': cookie.secure,
                    'httponly': cookie.httponly
                })
        return cookies
    except Exception as e:
        print(f"Error getting cookies: {e}")
        return []

def save_cookies_to_file(cookies, filename):
    """将cookie保存到文件"""
    with open(filename, 'w') as f:
        json.dump(cookies, f, indent=2)

if __name__ == "__main__":
    domain = "www.bilibili.com"
    cookies = get_chrome_cookies(domain)
    
    if cookies:
        print(f"Found {len(cookies)} cookies for {domain}")
        filename = "bilibili_cookies.txt"
        save_cookies_to_file(cookies, filename)
        print(f"Cookies saved to {filename}")
        
        # 显示cookie内容
        print("\nCookie content:")
        for cookie in cookies:
            print(f"{cookie['name']}: {cookie.value[:20]}...")
    else:
        print(f"No cookies found for {domain}")