"""
数据库模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Boolean, Float
from sqlalchemy.orm import relationship
from app.db.database import Base


class DeviceMemory(Base):
    """设备记忆表 - Dify agent 长期记忆"""
    __tablename__ = "device_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), unique=True, nullable=False, index=True)  # 设备唯一编号
    model = Column(String(100))  # 型号，如 IEVC-3.0
    device_name =  Column(String(50))#设备名称
    common_faults = Column(JSON, default=list)  # 历史故障 Top3 (JSON 数组)
    last_maintenance_date = Column(DateTime)  # 上次保养日期
    notes = Column(Text)  # 特殊备注
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SolutionHistory(Base):
    """历史解决方案表 - Dify agent 长期记忆"""
    __tablename__ = "solution_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    error_code = Column(String(20), index=True)  # 故障码
    symptoms = Column(Text)  # 故障现象描述
    solution = Column(Text)  # 成功解决方案
    solved_at = Column(DateTime, default=datetime.now, index=True)  # 解决日期
    created_at = Column(DateTime, default=datetime.now)
