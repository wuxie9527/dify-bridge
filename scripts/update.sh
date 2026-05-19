#!/bin/bash
set -e

echo "=========================================="
echo "  Dify Bridge - 快速更新脚本"
echo "=========================================="

PROJECT_DIR="/opt/dify-bridge"
cd $PROJECT_DIR

# 1. 拉取最新代码
echo ""
echo "📥 正在拉取最新代码..."
git pull origin main

# 2. 重新构建并重启（不删除数据卷）
echo ""
echo "🔄 正在重建服务..."
docker-compose up -d --build

# 3. 查看状态
echo ""
echo "=========================================="
echo "  更新完成！"
echo "=========================================="
echo ""
echo "📊 服务状态："
docker-compose ps

echo ""
echo "📋 查看日志：docker-compose logs -f"
