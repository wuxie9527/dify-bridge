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

# 2. 执行数据库迁移（如果存在新的迁移脚本）
echo ""
echo "📦 检查数据库迁移..."
if [ -f "migrations/001_add_diagnosis_memory.sql" ]; then
    # 检查表是否已存在
    TABLE_EXISTS=$(sqlite3 data/dify-bridge.db ".tables" | grep -c "diagnosis_memory" || echo "0")
    if [ "$TABLE_EXISTS" -eq 0 ]; then
        echo "🔧 执行数据库迁移..."
        sqlite3 data/dify-bridge.db < migrations/001_add_diagnosis_memory.sql
        echo "✓ 数据库迁移完成"
    else
        echo "✓ 数据库已是最新"
    fi
fi

# 3. 停止旧服务
echo ""
echo "🛑 正在停止旧服务..."
pkill -f "uvicorn app.main:app" || true

# 4. 启动新服务
echo ""
echo "🚀 正在启动新服务..."
nohup $PROJECT_DIR/venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 > logs/service.log 2>&1 &

sleep 3

# 5. 验证服务
echo ""
echo "🔍 验证服务..."
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✓ 服务启动成功"
else
    echo "⚠️  服务启动失败，请查看日志：tail -f logs/service.log"
fi

# 6. 查看状态
echo ""
echo "=========================================="
echo "  更新完成！"
echo "=========================================="
echo ""
echo "📊 服务状态："
ps aux | grep "uvicorn app.main:app" | grep -v grep || echo "⚠️  服务未启动"

echo ""
echo "📋 查看日志：tail -f logs/service.log"
