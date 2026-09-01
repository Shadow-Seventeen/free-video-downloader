#!/bin/bash

echo "=== 停止后端服务 ==="

# 停止所有相关进程
pkill -f "python main.py" 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "后端服务已停止"