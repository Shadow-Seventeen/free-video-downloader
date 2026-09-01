#!/bin/bash

echo "=== 启动后端服务 ==="

# 检查端口是否被占用
if lsof -i:8000 >/dev/null 2>&1; then
    echo "端口 8000 被占用，正在清理..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# 启动服务
echo "启动后端服务..."
cd "$(dirname "$0")"
python main.py