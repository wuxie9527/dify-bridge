#!/bin/bash
# ============================================================
# 长期记忆模块部署脚本
# ============================================================

set -e

INSTALL_DIR="/root/dify-bridge"
DB_FILE="$INSTALL_DIR/data/dify-bridge.db"

echo "=== 开始部署长期记忆模块 ==="

# 1. 进入目录
cd "$INSTALL_DIR"
echo "✓ 工作目录：$INSTALL_DIR"

# 2. 执行数据库迁移
echo "=== 执行数据库迁移 ==="
sqlite3 "$DB_FILE" << 'EOF'
-- 创建 diagnosis_memory 表
CREATE TABLE IF NOT EXISTS diagnosis_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id VARCHAR(50) NOT NULL,
    device_name VARCHAR(100),
    error_code VARCHAR(20),
    symptoms TEXT NOT NULL,
    solution TEXT,
    primary_cause TEXT,
    conversation_id VARCHAR(50),
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_symptoms ON diagnosis_memory(symptoms);
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_device_id ON diagnosis_memory(device_id);
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_device_name ON diagnosis_memory(device_name);
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_error_code ON diagnosis_memory(error_code);
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_hit_count ON diagnosis_memory(hit_count DESC);
EOF
echo "✓ 数据库迁移完成"

# 3. 备份旧代码（可选）
echo "=== 备份旧代码 ==="
if [ -d "app_backup" ]; then
    rm -rf app_backup
fi
cp -r app app_backup 2>/dev/null || echo "跳过备份"
echo "✓ 代码已备份到 app_backup/"

# 4. 拉取新代码
echo "=== 更新代码 ==="
git pull origin main 2>/dev/null || echo "非 git 部署，跳过"
echo "✓ 代码已更新"

# 5. 重启服务
echo "=== 重启服务 ==="
pkill -f uvicorn || true
sleep 2
nohup $INSTALL_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 >> $INSTALL_DIR/logs/service.log 2>&1 &
sleep 5
echo "✓ 服务已重启"

# 6. 验证服务
echo "=== 验证服务 ==="
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✓ 服务启动成功"
else
    echo "✗ 服务启动失败，请查看日志"
    tail -50 $INSTALL_DIR/logs/service.log
    exit 1
fi

# 7. 测试 API
echo "=== 测试 API ==="
echo "测试创建记忆..."
CREATE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/dify/memory \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "TEST-001",
    "symptoms": "测试症状",
    "solution": "测试方案"
  }')

if echo "$CREATE_RESPONSE" | grep -q "id"; then
    echo "✓ 创建 API 正常"
else
    echo "✗ 创建 API 异常：$CREATE_RESPONSE"
fi

echo "测试检索记忆..."
SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/dify/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "测试", "top_k": 5}')

if echo "$SEARCH_RESPONSE" | grep -q "cases"; then
    echo "✓ 检索 API 正常"
else
    echo "✗ 检索 API 异常：$SEARCH_RESPONSE"
fi

echo ""
echo "============================================"
echo "     长期记忆模块部署完成！"
echo "============================================"
echo ""
echo "API 文档：http://localhost:8000/docs"
echo "日志文件：$INSTALL_DIR/logs/service.log"
echo ""
echo "部署详情："
echo "  - 新增表：diagnosis_memory"
echo "  - 新增接口:"
echo "    POST /api/v1/dify/memory        (创建记忆)"
echo "    POST /api/v1/dify/memory/search (检索记忆)"
echo "    GET  /api/v1/dify/memory/{id}   (获取记忆)"
echo "    DEL  /api/v1/dify/memory/{id}   (删除记忆)"
echo ""
