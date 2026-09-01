#!/usr/bin/env python3
"""
完整的B站会员视频下载解决方案
包含Cookie获取、格式转换和测试功能
"""

import os
import json
import subprocess
from datetime import datetime, timezone, timedelta
import sys

def print_header(title):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def get_chrome_cookies_database():
    """从Chrome数据库获取Cookie"""
    print_header("从Chrome数据库获取B站Cookie")
    
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
        
        # 复制数据库到临时文件（避免数据库被锁定）
        import shutil
        import tempfile
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        shutil.copy2(db_path, temp_db.name)
        
        # 读取数据库
        import sqlite3
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        
        # 查询B站相关Cookie
        cursor.execute("""
            SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly 
            FROM cookies 
            WHERE host_key LIKE '%bilibili%' 
            ORDER BY name
        """)
        
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
        print(f"❌ 读取Cookie数据库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

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

def save_cookies_to_files(cookies):
    """保存Cookie到不同格式的文件"""
    print_header("保存Cookie文件")
    
    # 保存为JSON格式
    json_file = "bilibili_cookies.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=2)
    print(f"✅ JSON格式保存: {json_file}")
    
    # 转换为Netscape格式
    netscape_cookies = json_to_netscape(cookies)
    netscape_file = "bilibili_cookies.txt"
    with open(netscape_file, 'w', encoding='utf-8') as f:
        # 写入文件头注释
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# https://curl.se/docs/http-cookies.html\n")
        f.write("# This file was converted from JSON format\n\n")
        
        # 写入Cookie行
        for cookie in netscape_cookies:
            f.write(cookie + "\n")
    
    print(f"✅ Netscape格式保存: {netscape_file}")
    
    # 显示主要Cookie
    print("\n主要Cookie:")
    important_cookies = ['SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'sid']
    found_important = []
    
    for cookie in cookies:
        if cookie['name'] in important_cookies:
            found_important.append(cookie)
            print(f"  {cookie['name']}: {cookie['value'][:20]}...")
    
    if not found_important:
        print("⚠️ 未找到重要Cookie，可能需要重新获取")
    
    return netscape_file

def test_bilibili_download(netscape_file):
    """测试B站视频下载"""
    print_header("测试B站视频下载")
    
    if not os.path.exists(netscape_file):
        print(f"❌ Cookie文件不存在: {netscape_file}")
        return False
    
    try:
        from downloader import VideoDownloader
        
        downloader = VideoDownloader()
        
        # 测试URL（使用一个公开的B站视频URL）
        test_url = "https://www.bilibili.com/video/BV1GJ411x7h7"
        
        print(f"测试URL: {test_url}")
        
        # 测试解析视频
        print("\n1. 测试解析视频信息...")
        video_info = downloader.parse_video(test_url, netscape_file)
        print("✅ 视频解析成功!")
        print(f"   标题: {video_info['title']}")
        print(f"   时长: {video_info['duration_string']}")
        print(f"   平台: {video_info['platform']}")
        print(f"   格式数量: {len(video_info['formats'])}")
        
        # 检查是否有会员相关标识
        if video_info.get('platform') == 'Bilibili':
            print("✅ 这是B站视频")
            
            # 检查格式中是否有会员标识
            has_member_format = any('会员' in f.get('label', '') for f in video_info['formats'])
            if has_member_format:
                print("✅ 检测到会员视频格式")
            else:
                print("⚠️ 未检测到会员视频格式，但可能是普通视频")
        
        # 测试获取直链
        print("\n2. 测试获取直链...")
        direct_url = downloader.get_direct_url(test_url, "best", netscape_file)
        print("✅ 直链获取成功!")
        print(f"   直链: {direct_url['direct_url'][:50]}...")
        print(f"   文件大小: {direct_url.get('filesize', '未知')}")
        
        print("\n🎉 所有测试通过! B站Cookie功能正常工作。")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_usage_guide():
    """创建使用指南"""
    guide = """
# B站会员视频下载完整使用指南

## 概述
这个解决方案提供了完整的B站会员视频下载功能，包括：
1. 从Chrome浏览器自动获取B站Cookie
2. 将Cookie转换为yt-dlp所需的Netscape格式
3. 测试Cookie功能是否正常

## 使用步骤

### 1. 运行完整解决方案
```bash
cd backend
python complete_bilibili_solution.py
```

### 2. 使用生成的Cookie文件
成功运行后，你会得到以下文件：
- `bilibili_cookies.json` - JSON格式的Cookie文件
- `bilibili_cookies.txt` - Netscape格式的Cookie文件（推荐使用）

### 3. 在代码中使用Cookie

#### 解析视频信息
```python
from downloader import VideoDownloader

downloader = VideoDownloader()
video_info = downloader.parse_video(
    "https://www.bilibili.com/video/BV1xxxxxxx",
    "bilibili_cookies.txt"
)
```

#### 下载视频
```python
download_result = downloader.download_video(
    "https://www.bilibili.com/video/BV1xxxxxxx",
    "best",
    "bilibili_cookies.txt"
)
```

#### 获取直链
```python
direct_url = downloader.get_direct_url(
    "https://www.bilibili.com/video/BV1xxxxxxx",
    "best",
    "bilibili_cookies.txt"
)
```

### 4. API调用示例

#### 解析视频
```bash
curl -X POST "http://localhost:8000/api/parse" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://www.bilibili.com/video/BV1xxxxxxx",
    "cookies": "bilibili_cookies.txt"
  }'
```

#### 下载视频
```bash
curl -X POST "http://localhost:8000/api/download" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://www.bilibili.com/video/BV1xxxxxxx",
    "format_id": "best",
    "cookies": "bilibili_cookies.txt"
  }'
```

## 故障排除

### 问题1：Cookie获取失败
**解决方案：**
1. 确保Chrome浏览器已打开并登录B站
2. 检查Chrome浏览器是否正常运行
3. 如果仍有问题，可以手动创建Cookie文件

### 问题2：HTTP 412错误
**解决方案：**
1. Cookie可能已过期，重新获取Cookie
2. 请求头信息可能不完整，需要添加更多头部
3. B站可能更新了反爬虫机制

### 问题3：视频无法下载
**解决方案：**
1. 检查视频URL是否正确
2. 确认该视频确实是B站会员视频
3. 尝试不同的format_id
4. 重新获取Cookie

## 重要提示

1. **Cookie有效期**：Cookie通常有有效期，过期后需要重新获取
2. **定期更新**：建议定期更新Cookie以确保功能正常
3. **合法使用**：请遵守B站的服务条款和相关法律法规
4. **隐私保护**：Cookie包含敏感信息，请妥善保管

## 自动化脚本

### 重新获取Cookie
```bash
python complete_bilibili_solution.py
```

### 测试Cookie功能
```bash
python test_bilibili_with_cookies.py
```

## 总结

这个解决方案提供了完整的B站会员视频下载功能。通过自动化获取和转换Cookie，你可以轻松下载B站的会员视频。记得定期更新Cookie以确保功能正常工作。
"""
    
    with open("B站会员视频下载完整指南.md", 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ 已创建完整使用指南: B站会员视频下载完整指南.md")

def main():
    """主函数"""
    print_header("B站会员视频下载完整解决方案")
    
    # 检查是否已存在Cookie文件
    if os.path.exists("bilibili_cookies.txt"):
        print("发现现有的Cookie文件，是否覆盖？")
        try:
            choice = input("输入 'y' 覆盖，其他键跳过: ").lower()
            if choice != 'y':
                netscape_file = "bilibili_cookies.txt"
                if test_bilibili_download(netscape_file):
                    print("✅ 使用现有Cookie测试成功")
                return
        except EOFError:
            # 非交互式环境，直接使用现有Cookie
            print("⚠️ 检测到非交互式环境，使用现有Cookie文件")
            netscape_file = "bilibili_cookies.txt"
            if test_bilibili_download(netscape_file):
                print("✅ 使用现有Cookie测试成功")
            else:
                print("⚠️ 测试失败，将重新获取Cookie")
                # 继续执行获取Cookie的逻辑
    
    # 获取Cookie
    cookies = get_chrome_cookies_database()
    
    if cookies:
        # 保存Cookie文件
        netscape_file = save_cookies_to_files(cookies)
        
        # 测试下载功能
        if test_bilibili_download(netscape_file):
            print("\n🎉 所有功能正常工作!")
            
            # 创建使用指南
            create_usage_guide()
            
            print("\n📚 已创建完整使用指南")
            print("🔗 推荐阅读: B站会员视频下载完整指南.md")
        else:
            print("\n⚠️ 测试失败，请检查Cookie是否有效")
    else:
        print("\n❌ Cookie获取失败，请检查错误信息并重试")

if __name__ == "__main__":
    main()