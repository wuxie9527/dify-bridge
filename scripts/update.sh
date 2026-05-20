#!/bin/bash
set -e

PROJECT_DIR="/root/dify-bridge"
cd $PROJECT_DIR

echo "=========================================="
echo "  Dify Bridge - 快速更新脚本"
echo "=========================================="

# 激活虚拟环境（使用绝对路径）
export PATH="$PROJECT_DIR/venv/bin:$PATH"

# 1. 拉取最新代码
echo ""
echo "📥 正在拉取最新代码..."
git pull origin main

# 2. 停止旧服务
echo ""
echo "🛑 正在停止旧服务..."
pkill -f "uvicorn app.main:app" || true

# 3. 启动新服务
echo ""
echo "🚀 正在启动新服务..."
nohup python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 > logs/service.log 2>&1 &

sleep 2

# 4. 查看状态
echo ""
echo "=========================================="
echo "  更新完成！"
echo "=========================================="
echo ""
echo "📊 服务状态："
ps aux | grep "uvicorn app.main:app" | grep -v grep || echo "⚠️  服务未启动"

echo ""
echo "📋 查看日志：tail -f logs/service.log"
