-- 长期记忆表迁移脚本
-- 执行方式：sqlite3 data/dify-bridge.db < migrations/001_add_diagnosis_memory.sql

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

-- 创建索引加速检索
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_symptoms ON diagnosis_memory(symptoms);
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_device_id ON diagnosis_memory(device_id);
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_device_name ON diagnosis_memory(device_name);
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_error_code ON diagnosis_memory(error_code);
CREATE INDEX IF NOT EXISTS idx_diagnosis_memory_hit_count ON diagnosis_memory(hit_count DESC);

-- 验证表已创建
-- .tables diagnosis_memory
-- PRAGMA table_info(diagnosis_memory);
