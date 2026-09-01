#!/usr/bin/env python3
"""
简化的B站Cookie获取工具
避免钥匙串权限问题
"""

import os
import json
import subprocess
from pathlib import Path
import re

def get_chrome_cookies():
    """通过命令行工具获取Chrome Cookie"""
    try:
        print("尝试通过命令行获取Chrome Cookie...")
        
        # 方法1：使用sqlite3直接读取Cookie数据库
        cookies = read_chrome_cookies_directly()
        if cookies:
            return cookies
        
        # 方法2：使用Python sqlite3
        cookies = read_chrome_cookies_python()
        if cookies:
            return cookies
        
        print("❌ 无法直接读取Cookie数据库")
        return None
        
    except Exception as e:
        print(f"❌ 获取Cookie失败: {str(e)}")
        return None

def read_chrome_cookies_directly():
    """直接读取Chrome Cookie数据库"""
    try:
        # Chrome Cookie数据库路径
        chrome_paths = [
            os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies"),
            os.path.expanduser("~/Library/Application Support/Chromium/Default/Cookies"),
        ]
        
        # 检查数据库是否存在
        db_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if not db_path:
            print("❌ 未找到Chrome Cookie数据库")
            return None
        
        print(f"✅ 找到Cookie数据库: {db_path}")
        
        # 使用命令行读取SQLite
        cmd = f'''
        sqlite3 "{db_path}" "
        SELECT name, value, host_key, path, expires, is_secure, is_httponly 
        FROM cookies 
        WHERE host_key LIKE '%bilibili%' 
        ORDER BY name;
        "
        '''
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ SQLite查询失败: {result.stderr}")
            return None
        
        cookies = []
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if line:
                parts = line.split('|')
                if len(parts) >= 7:
                    cookies.append({
                        'name': parts[0],
                        'value': parts[1],
                        'domain': parts[2],
                        'path': parts[3],
                        'expires': int(parts[4]),
                        'secure': bool(int(parts[5])),
                        'httponly': bool(int(parts[6]))
                    })
        
        if cookies:
            print(f"✅ 找到 {len(cookies)} 个B站Cookie")
            return cookies
        else:
            print("❌ 未找到B站Cookie")
            return None
        
    except Exception as e:
        print(f"❌ 直接读取Cookie数据库失败: {str(e)}")
        return None

def read_chrome_cookies_python():
    """使用Python读取Chrome Cookie数据库"""
    try:
        import sqlite3
        
        # Chrome Cookie数据库路径
        chrome_paths = [
            os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies"),
            os.path.expanduser("~/Library/Application Support/Chromium/Default/Cookies"),
        ]
        
        # 检查数据库是否存在
        db_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if not db_path:
            print("❌ 未找到Chrome Cookie数据库")
            return None
        
        print(f"✅ 找到Cookie数据库: {db_path}")
        
        # 复制数据库到临时文件（避免数据库被锁定）
        import shutil
        import tempfile
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        shutil.copy2(db_path, temp_db.name)
        
        # 读取数据库
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        
        # 查询B站相关Cookie
        cursor.execute("SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly FROM cookies WHERE host_key LIKE '%bilibili%' ORDER BY name")
        results = cursor.fetchall()
        conn.close()
        
        # 删除临时文件
        os.unlink(temp_db.name)
        
        cookies = []
        for result in results:
            if len(result) >= 7:
                name, value, host_key, path, expires_utc, is_secure, is_httponly = result
                cookies.append({
                    'name': name,
                    'value': value,
                    'domain': host_key,
                    'path': path,
                    'expires': expires_utc if expires_utc else 0,
                    'secure': bool(is_secure),
                    'httponly': bool(is_httponly)
                })
        
        if cookies:
            print(f"✅ 找到 {len(cookies)} 个B站Cookie")
            return cookies
        else:
            print("❌ 未找到B站Cookie")
            return None
        
    except Exception as e:
        print(f"❌ Python读取Cookie数据库失败: {str(e)}")
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
    
    # 检查是否在交互式环境中
    try:
        # 尝试读取Cookie
        print("请输入B站Cookie（输入完成后按回车键）:")
        print("如果你在交互式环境中，可以直接输入：")
        print("SESSDATA=你的SESSDATA值")
        print("bili_jct=你的bili_jct值")
        print("DedeUserID=你的用户ID")
        print("")
        
        # 模拟输入（如果无法交互式输入）
        sample_cookies = [
            ("SESSDATA", "your_sessdata_here"),
            ("bili_jct", "your_bili_jct_here"),
            ("DedeUserID", "your_user_id_here"),
            ("DedeUserID__ckMd5", "your_user_hash_here"),
            ("sid", "your_session_id_here")
        ]
        
        print("示例Cookie（请替换为你的实际值）：")
        for name, value in sample_cookies:
            print(f"{name}={value}")
        
        # 如果不是交互式环境，创建示例Cookie
        cookies = []
        print("\n⚠️ 注意：由于无法交互式输入，请手动创建Cookie文件")
        print(f"请编辑文件：{os.path.abspath('bilibili_cookies.txt')}")
        print("格式如下：")
        
        sample_data = [
            {
                'name': 'SESSDATA',
                'value': '你的实际SESSDATA值',
                'domain': '.bilibili.com',
                'path': '/',
                'expires': 1800000000,
                'secure': True,
                'httponly': False
            },
            {
                'name': 'bili_jct',
                'value': '你的实际bili_jct值',
                'domain': '.bilibili.com',
                'path': '/',
                'expires': 1800000000,
                'secure': True,
                'httponly': False
            }
        ]
        
        with open("bilibili_cookies_template.txt", 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        print("✅ 已创建Cookie模板文件：bilibili_cookies_template.txt")
        print("请用你的实际Cookie值替换模板中的值，然后重命名为bilibili_cookies.txt")
        
        return None
        
    except EOFError:
        print("\n⚠️ 检测到非交互式环境")
        print("请手动创建Cookie文件，格式参考bilibili_cookies_template.txt")
        return None

def save_cookies_to_file(cookies):
    """保存Cookie到文件"""
    if not cookies:
        print("❌ 没有可保存的Cookie")
        return None
    
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

def main():
    """主函数"""
    print("=== 简化的B站Cookie获取工具 ===")
    print("这个工具尝试多种方法获取B站Cookie，避免钥匙串权限问题")
    print()
    
    # 检查是否已经存在Cookie文件
    cookies_file = "bilibili_cookies.txt"
    if os.path.exists(cookies_file):
        print(f"发现现有的Cookie文件: {cookies_file}")
        choice = input("是否覆盖现有Cookie文件? (y/n): ").lower()
        if choice != 'y':
            print("使用现有Cookie文件...")
            return
    
    # 尝试获取Cookie
    cookies = get_chrome_cookies()
    
    if cookies:
        save_cookies_to_file(cookies)
        print(f"\n✅ Cookie获取成功!")
        print(f"文件路径: {os.path.abspath(cookies_file)}")
    else:
        print("\n自动获取失败，请手动输入Cookie：")
        cookies = manual_input_cookies()
        if cookies:
            save_cookies_to_file(cookies)
        else:
            print("\n❌ Cookie获取失败，请检查错误信息并重试")

if __name__ == "__main__":
    main()