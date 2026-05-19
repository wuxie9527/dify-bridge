#!/bin/bash
set -e

echo "=========================================="
echo "  Dify Bridge - 部署脚本"
echo "=========================================="

PROJECT_DIR="/opt/dify-bridge"
cd $PROJECT_DIR

# 1. 拉取最新代码
echo ""
echo "📥 正在拉取最新代码..."
git fetch origin main
git reset --hard origin/main
echo "✅ 代码拉取完成"

# 2. 检查 .env 是否存在
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  .env 文件不存在，从 .env.example 复制"
    cp .env.example .env
    echo "❌ 请编辑 .env 文件配置必要的环境变量，然后重新运行此脚本"
    echo "   命令：vi .env"
    exit 1
fi

# 3. 停止旧服务
echo ""
echo "🛑 正在停止旧服务..."
docker-compose down || true

# 4. 构建新镜像
echo ""
echo "🔨 正在构建 Docker 镜像..."
docker-compose build --no-cache

# 5. 启动新服务
echo ""
echo "🚀 正在启动新服务..."
docker-compose up -d

# 6. 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 7. 查看状态
echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "📊 服务状态："
docker-compose ps

echo ""
echo "📋 常用命令："
echo "   查看日志：docker-compose logs -f"
echo "   停止服务：docker-compose down"
echo "   重启服务：docker-compose restart"
echo "   进入容器：docker exec -it dify-bridge bash"
echo ""

# 8. 健康检查
echo "🏥 健康检查..."
curl -s http://localhost:8000/health | jq '.' || echo "⚠️  健康检查失败，请查看日志"
