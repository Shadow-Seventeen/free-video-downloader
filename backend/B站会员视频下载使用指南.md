# B站会员视频下载使用指南

## 概述

本文档介绍如何使用新增的B站会员视频下载功能。通过集成Cookie认证，系统现在可以下载B站的会员视频。

## 前置条件

1. 已登录B站网站（Chrome浏览器）
2. 已安装browser-cookie3库：`pip install browser-cookie3`
3. 有一个B站会员视频URL

## 步骤1：获取B站Cookie

### 运行Cookie获取工具

```bash
cd backend
python bilibili_cookies_helper.py
```

### 工具说明

1. 打开B站网站并登录（确保Chrome浏览器已打开）
2. 运行Cookie获取工具
3. 工具会自动从Chrome浏览器中提取B站的Cookie
4. Cookie将保存为`bilibili_cookies.txt`文件

### 重要Cookie

以下Cookie对于下载会员视频至关重要：
- SESSDATA：会话ID
- bili_jct： CSRF令牌
- DedeUserID：用户ID
- DedeUserID__ckMd5：用户ID哈希
- sid：会话ID

## 步骤2：下载B站会员视频

### API调用示例

#### 1. 解析视频信息

```bash
curl -X POST "http://localhost:8000/api/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BV1xxxxxxx",
    "cookies": "bilibili_cookies.txt"
  }'
```

#### 2. 获取直链

```bash
curl -X POST "http://localhost:8000/api/direct-url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BV1xxxxxxx",
    "format_id": "best",
    "cookies": "bilibili_cookies.txt"
  }'
```

#### 3. 下载视频

```bash
curl -X POST "http://localhost:8000/api/download" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bilibili.com/video/BV1xxxxxxx",
    "format_id": "best",
    "cookies": "bilibili_cookies.txt"
  }'
```

### 前端集成示例

```javascript
// 解析B站会员视频
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

const parseData = await parseResponse.json();
console.log('视频信息:', parseData);

// 下载B站会员视频
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

// 处理下载响应...
```

## 技术实现

### 1. 代码修改

#### downloader.py
- 添加了`cookies`参数到所有主要方法
- 支持yt-dlp的`cookiefile`选项

#### main.py
- 修改了所有相关API端点，支持传递Cookie
- 更新了请求模型，添加`cookies`字段

### 2. Cookie处理

- 从Chrome浏览器自动获取Cookie
- 保存为标准Netscape格式Cookie文件
- yt-dlp通过`cookiefile`选项使用Cookie

### 3. 错误处理

- Cookie失效时会提示重新获取
- 网络错误会返回详细的错误信息
- 视频解析失败会返回具体原因

## 故障排除

### 1. Cookie获取失败

**问题：** 无法从Chrome浏览器获取Cookie
**解决方案：**
- 确保Chrome浏览器已打开并登录B站
- 检查browser-cookie3是否正确安装
- 尝试手动保存Cookie到文件

### 2. 会员视频无法下载

**问题：** 使用Cookie后仍然无法下载会员视频
**解决方案：**
- 检查Cookie是否过期（重新运行Cookie获取工具）
- 确保视频确实是会员视频
- 尝试不同的`format_id`

### 3. 网络错误

**问题：** 下载过程中出现网络错误
**解决方案：**
- 检查网络连接
- 尝试重试下载
- 使用更小的`format_id`

## 最佳实践

1. **定期更新Cookie**：Cookie通常有一定有效期，建议定期更新
2. **使用合适的格式**：对于会员视频，建议使用`bestvideo+bestaudio`格式
3. **错误重试机制**：下载失败时自动重试，但不要频繁重试
4. **Cookie文件管理**：管理多个Cookie文件，便于不同用户使用

## 注意事项

1. **合法使用**：仅下载自己拥有版权或已获得合法授权的内容
2. **遵守服务条款**：请遵守B站的服务条款和相关规定
3. **隐私保护**：Cookie包含敏感信息，请妥善保管
4. **性能考虑**：频繁下载可能会触发B站的限制机制

## API参考

### ParseRequest
```json
{
  "url": "string",
  "cookies": "string (可选)"
}
```

### DownloadRequest
```json
{
  "url": "string",
  "format_id": "string",
  "cookies": "string (可选)"
}
```

### 响应格式
```json
{
  "success": boolean,
  "data": object,
  "error": string (仅在失败时)
}
```

## 总结

通过这个新增功能，用户现在可以下载B站的会员视频。只需提供B站Cookie，系统就可以访问会员专属内容。这个功能扩展了视频下载器的范围，使其能够处理更多类型的B站内容。