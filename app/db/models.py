"""
数据库模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.db.database import Base


class DiagnosisMemory(Base):
    """长期记忆表 - 诊断案例记忆（支持关键词检索）"""
    __tablename__ = "diagnosis_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)  # 设备编号
    device_name = Column(String(100), index=True)  # 设备名称
    error_code = Column(String(20), index=True)  # 故障码
    symptoms = Column(Text, nullable=False, index=True)  # 症状描述（检索用）
    solution = Column(Text)  # 解决方案
    primary_cause = Column(Text)  # 根本原因
    conversation_id = Column(String(50))  # 会话 ID
    hit_count = Column(Integer, default=0)  # 命中次数
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
