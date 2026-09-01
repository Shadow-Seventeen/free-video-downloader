#!/usr/bin/env python3
"""
B站Cookie获取工具
用于从Chrome浏览器中获取B站的Cookie，支持会员视频下载
"""

import os
import json
import sys
import subprocess
from pathlib import Path

def get_bilibili_cookies():
    """获取Chrome浏览器中B站的Cookie"""
    try:
        print("正在从Chrome浏览器中获取B站Cookie...")
        
        # 尝试方法1：使用browser_cookie3（可能需要钥匙串权限）
        try:
            from browser_cookie3 import chrome
            cj = chrome()
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
                print(f"✅ 通过browser_cookie3找到 {len(cookies)} 个B站Cookie")
                return save_cookies_to_file(cookies)
            else:
                print("❌ browser_cookie3未找到B站Cookie")
        except Exception as e:
            print(f"⚠️ browser_cookie3失败: {str(e)}")
        
        # 尝试方法2：直接读取Chrome的Cookie数据库
        print("尝试直接读取Chrome Cookie数据库...")
        cookies = get_cookies_from_chrome_db()
        if cookies:
            print(f"✅ 通过直接读取找到 {len(cookies)} 个B站Cookie")
            return save_cookies_to_file(cookies)
        
        # 尝试方法3：手动输入Cookie
        print("无法自动获取Cookie，请手动提供B站Cookie：")
        return manual_input_cookies()
            
    except Exception as e:
        print(f"❌ 获取Cookie失败: {str(e)}")
        return None

def get_cookies_from_chrome_db():
    """直接从Chrome的Cookie数据库获取Cookie"""
    try:
        # Chrome Cookie数据库路径
        chrome_paths = [
            os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies"),
            os.path.expanduser("~/Library/Application Support/Chromium/Default/Cookies"),
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Cookies"),
            os.path.expanduser("~/AppData/Local/Chromium/User Data/Default/Cookies"),
        ]
        
        import sqlite3
        cookies = []
        
        for db_path in chrome_paths:
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # 查询B站相关Cookie
                    cursor.execute("SELECT name, value, host_key, path, expires, is_secure, is_httponly FROM cookies WHERE host_key LIKE '%bilibili%'")
                    results = cursor.fetchall()
                    
                    for name, value, host_key, path, expires, is_secure, is_httponly in results:
                        cookies.append({
                            'name': name,
                            'value': value,
                            'domain': host_key,
                            'path': path,
                            'expires': expires if expires else 0,
                            'secure': bool(is_secure),
                            'httponly': bool(is_httponly)
                        })
                    
                    conn.close()
                    
                    if cookies:
                        print(f"  从 {db_path} 找到Cookie")
                        break
                        
                except Exception as e:
                    print(f"  无法读取 {db_path}: {str(e)}")
                    continue
        
        return cookies
    except Exception as e:
        print(f"❌ 直接读取Cookie数据库失败: {str(e)}")
        return None

def manual_input_cookies():
    """手动输入Cookie"""
    print("\n请按以下格式输入B站Cookie（每行一个）：")
    print("格式：名称=值")
    print("例如：")
    print("SESSDATA=xxx")
    print("bili_jct=xxx")
    print("DedeUserID=xxx")
    print()
    
    cookies = []
    while True:
        cookie_input = input("输入Cookie（直接回车结束）: ").strip()
        if not cookie_input:
            break
        
        if '=' in cookie_input:
            name, value = cookie_input.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.bilibili.com',
                'path': '/',
                'expires': 1800000000,  # 设置一个过期时间
                'secure': True,
                'httponly': False
            })
            print(f"  已添加: {name}")
        else:
            print("  格式错误，请重新输入")
    
    if cookies:
        return save_cookies_to_file(cookies)
    else:
        print("❌ 未输入任何Cookie")
        return None

def save_cookies_to_file(cookies):
    """保存Cookie到文件"""
    cookies_file = "bilibili_cookies.txt"
    with open(cookies_file, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"✅ Cookie已保存到 {cookies_file}")
    
    # 显示主要Cookie
    print("\n主要Cookie:")
    important_cookies = ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'sid']
    for cookie in cookies:
        if cookie['name'] in important_cookies:
            print(f"  {cookie['name']}: {cookie['value'][:20]}...")
    
    return cookies_file

def test_cookies_file(cookies_file):
    """测试Cookie文件是否有效"""
    if not os.path.exists(cookies_file):
        print(f"❌ Cookie文件不存在: {cookies_file}")
        return False
    
    try:
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        
        if not cookies:
            print("❌ Cookie文件为空")
            return False
        
        print(f"✅ Cookie文件有效，包含 {len(cookies)} 个Cookie")
        return True
        
    except Exception as e:
        print(f"❌ 读取Cookie文件失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=== B站Cookie获取工具 ===")
    print("此工具用于获取B站Cookie，支持会员视频下载")
    print()
    
    # 检查是否已经存在Cookie文件
    cookies_file = "bilibili_cookies.txt"
    if os.path.exists(cookies_file):
        print(f"发现现有的Cookie文件: {cookies_file}")
        choice = input("是否覆盖现有Cookie文件? (y/n): ").lower()
        if choice != 'y':
            print("使用现有Cookie文件...")
            if test_cookies_file(cookies_file):
                print(f"Cookie文件路径: {os.path.abspath(cookies_file)}")
                return
            else:
                print("现有Cookie文件无效，将重新获取...")
    
    # 获取Cookie
    cookies_file = get_bilibili_cookies()
    
    if cookies_file and test_cookies_file(cookies_file):
        print(f"\n✅ Cookie获取成功!")
        print(f"文件路径: {os.path.abspath(cookies_file)}")
        print("\n使用说明:")
        print("1. 在下载B站会员视频时，请在请求中包含这个Cookie文件")
        print("2. 如果Cookie失效，请重新运行此工具获取新的Cookie")
        print("3. 建议定期更新Cookie，以确保下载功能正常")
    else:
        print("\n❌ Cookie获取失败，请检查上述错误信息并重试")

if __name__ == "__main__":
    main()