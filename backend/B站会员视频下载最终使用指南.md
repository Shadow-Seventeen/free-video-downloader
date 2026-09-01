# B站会员视频下载最终使用指南

## 📋 问题总结

经过详细的分析和测试，我们成功实现了B站会员视频下载功能。以下是完整的解决方案：

## ✅ 已完成的工作

### 1. 代码修改
- ✅ 修改了 `downloader.py`，添加了 `cookies` 参数支持
- ✅ 修改了 `main.py`，更新了API端点以支持cookies参数
- ✅ 创建了Cookie获取工具和格式转换工具

### 2. Cookie功能
- ✅ 可以从Chrome浏览器自动获取B站Cookie
- ✅ 支持将Cookie转换为yt-dlp所需的Netscape格式
- ✅ 生成了 `bilibili_cookies.txt` 文件

## 🚀 具体使用步骤

### 步骤1：获取B站Cookie

```bash
cd backend
python get_bilibili_cookies_simple.py
```

**如果遇到钥匙串权限问题：**
1. 在Chrome浏览器中登录B站
2. 运行上述脚本
3. 如果弹出钥匙串访问提示，输入你的macOS用户密码
4. 如果仍然失败，工具会自动尝试其他方法

### 步骤2：转换Cookie格式

```bash
python convert_cookies_to_netscape.py
```

这会将JSON格式的Cookie转换为yt-dlp所需的Netscape格式。

### 步骤3：使用Cookie下载B站视频

#### 方法1：Python代码直接调用

```python
from downloader import VideoDownloader

downloader = VideoDownloader()

# 解析视频信息
video_info = downloader.parse_video(
    "https://www.bilibili.com/video/BV1xxxxxxx",
    "bilibili_cookies.txt"
)

# 下载视频
download_result = downloader.download_video(
    "https://www.bilibili.com/video/BV1xxxxxxx",
    "best",
    "bilibili_cookies.txt"
)

# 获取直链
direct_url = downloader.get_direct_url(
    "https://www.bilibili.com/video/BV1xxxxxxx",
    "best",
    "bilibili_cookies.txt"
)
```

#### 方法2：API调用

```bash
# 解析视频信息
curl -X POST "http://localhost:8000/api/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BV1xxxxxxx",
    "cookies": "bilibili_cookies.txt"
  }'

# 下载视频
curl -X POST "http://localhost:8000/api/download" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BV1xxxxxxx",
    "format_id": "best",
    "cookies": "bilibili_cookies.txt"
  }'
```

#### 方法3：前端集成

```javascript
// 解析B站视频
const parseResponse = await fetch('/api/parse', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://www.bilibili.com/video/BV1xxxxxxx',
    cookies: 'bilibili_cookies.txt'
  })
});

// 下载B站视频
const downloadResponse = await fetch('/api/download', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://www.bilibili.com/video/BV1xxxxxxx',
    format_id: 'best',
    cookies: 'bilibili_cookies.txt'
  })
});
```

## ⚠️ 注意事项

### 1. HTTP 412错误
如果遇到HTTP 412错误，这通常意味着：
- Cookie可能已过期，需要重新获取
- B站的反爬虫机制检测到了异常请求
- 需要添加更多的请求头信息

**解决方案：**
1. 重新运行Cookie获取工具
2. 确保Chrome浏览器已登录B站
3. 尝试不同的视频URL

### 2. Cookie有效期
- Cookie通常有一定的有效期（几天到几周）
- 过期后需要重新获取
- 建议定期更新Cookie

### 3. 文件位置
确保Cookie文件在正确的位置：
- Cookie文件应该在 `backend` 目录下
- 文件名应该是 `bilibili_cookies.txt`

## 🔧 故障排除

### 问题1：Cookie获取失败
**原因：** 钥匙串权限问题或Chrome未登录
**解决方案：**
1. 确保Chrome浏览器已打开并登录B站
2. 接受钥匙串访问权限（输入macOS密码）
3. 或使用手动方法获取Cookie

### 问题2：视频无法下载
**原因：** Cookie过期或视频URL错误
**解决方案：**
1. 重新获取Cookie
2. 检查视频URL是否正确
3. 确认视频确实是B站会员视频

### 问题3：格式错误
**原因：** Cookie文件格式不正确
**解决方案：**
1. 运行 `convert_cookies_to_netscape.py`
2. 确保使用Netscape格式的Cookie文件

## 📝 手动获取Cookie（备选方案）

如果自动获取失败，可以手动创建Cookie文件：

1. 在Chrome浏览器中打开B站并登录
2. 按F12打开开发者工具
3. 选择"Application" > "Storage" > "Cookies" > "https://www.bilibili.com"
4. 复制主要Cookie的值：
   - SESSDATA
   - bili_jct
   - DedeUserID
   - DedeUserID__ckMd5
   - sid

5. 创建 `bilibili_cookies.txt` 文件，格式如下：

```
# Netscape HTTP Cookie File
.bilibili.com	TRUE	/	TRUE	1800000000	SESSDATA	你的SESSDATA值
.bilibili.com	TRUE	/	TRUE	1800000000	bili_jct	你的bili_jct值
.bilibili.com	TRUE	/	TRUE	1800000000	DedeUserID	你的用户ID
.bilibili.com	TRUE	/	TRUE	1800000000	DedeUserID__ckMd5	你的用户ID哈希
.bilibili.com	TRUE	/	FALSE	1800000000	sid	你的会话ID
```

## 🎉 成功标志

当你成功下载B站会员视频时，你会看到：
- ✅ 视频解析成功，返回视频标题、时长等信息
- ✅ 获取到直链或下载成功
- ✅ 文件保存在 `downloads` 目录下

## 📞 支持

如果遇到问题，请检查：
1. Chrome浏览器是否已登录B站
2. Cookie文件是否存在且格式正确
3. 视频URL是否正确
4. 后端服务是否正常运行

## 🔒 安全提示

- Cookie包含敏感信息，请妥善保管
- 不要将Cookie文件分享给他人
- 定期更新Cookie以确保安全
- 遵守B站的服务条款和相关法律法规

---

**最后更新时间：** 2024年
**适用版本：** yt-dlp 2026.1.0+
**支持平台：** macOS, Windows, Linux