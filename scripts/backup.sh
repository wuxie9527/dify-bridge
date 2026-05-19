#!/bin/bash
set -e

echo "=========================================="
echo "  Dify Bridge - 备份脚本"
echo "=========================================="

BACKUP_DIR="/opt/backups/dify-bridge"
DATA_DIR="/opt/dify-bridge/data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

echo ""
echo "📦 正在备份数据..."

# 备份数据库
if [ -f "$DATA_DIR/battery.db" ]; then
    cp $DATA_DIR/battery.db $BACKUP_DIR/battery_${TIMESTAMP}.db
    echo "✅ 数据库备份完成：battery_${TIMESTAMP}.db"
else
    echo "⚠️  数据库文件不存在"
fi

# 备份日志（可选）
if [ -d "$DATA_DIR/logs" ]; then
    tar -czf $BACKUP_DIR/logs_${TIMESTAMP}.tar.gz -C $DATA_DIR logs
    echo "✅ 日志备份完成：logs_${TIMESTAMP}.tar.gz"
fi

echo ""
echo "🧹 清理 7 天前的备份..."
find $BACKUP_DIR -name "battery_*.db" -mtime +7 -delete
find $BACKUP_DIR -name "logs_*.tar.gz" -mtime +7 -delete

echo ""
echo "=========================================="
echo "  备份完成！"
echo "=========================================="
echo ""
echo "备份目录：$BACKUP_DIR"
ls -lh $BACKUP_DIR
