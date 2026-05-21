"""
诊断相关 Schema
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DeviceUpdateInput(BaseModel):
    """设备更新输入"""
    model: Optional[str] = Field(default=None, description="型号，如 IEVC-3.0")
    device_name: Optional[str] = Field(default=None, description="设备名称")
    common_faults: Optional[list] = Field(default=None, description="常见故障 Top3")
    last_maintenance_date: Optional[str] = Field(default=None, description="上次保养日期")
    notes: Optional[str] = Field(default=None, description="备注")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "IEVC-3.0",
                "device_name": "1 号充电桩",
                "common_faults": ["E001", "E003"],
                "last_maintenance_date": "2024-01-15",
                "notes": "需要定期更换冷却液"
            }
        }


class SimilarCaseQuery(BaseModel):
    """相似案例查询"""
    error_code: Optional[str] = Field(default=None, description="故障码", max_length=20)
    symptoms: Optional[str] = Field(default=None, description="症状描述")
    limit: int = Field(default=5, description="返回数量限制", ge=1, le=20)

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "E003",
                "symptoms": "温度异常，显示 -40 度",
                "limit": 5
            }
        }


class SolutionRecord(BaseModel):
    """解决方案记录"""
    error_code: str = Field(..., description="故障码")
    symptoms: str = Field(..., description="故障现象描述")
    solution: str = Field(..., description="成功解决方案")
    solved_at: Optional[datetime] = Field(default=None, description="解决日期")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "E003",
                "symptoms": "温度显示 -40 度，插头腐蚀",
                "solution": "清洗插头，涂抹接触保护剂，重新安装",
                "solved_at": "2024-01-15 14:30:00"
            }
        }


# ========== 长期记忆模块 ==========

class MemoryCreate(BaseModel):
    """创建记忆 - 诊断完成后写入"""
    device_id: str = Field(..., description="设备编号")
    device_name: Optional[str] = Field(default=None, description="设备名称")
    error_code: Optional[str] = Field(default=None, description="故障码")
    symptoms: str = Field(..., description="症状描述")
    solution: Optional[str] = Field(default=None, description="解决方案")
    primary_cause: Optional[str] = Field(default=None, description="根本原因")
    conversation_id: Optional[str] = Field(default=None, description="会话 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "IEVC-3.0-001",
                "device_name": "1 号充电桩",
                "error_code": "E001",
                "symptoms": "充电时突然断电",
                "solution": "检查充电模块保险丝",
                "primary_cause": "保险丝熔断",
                "conversation_id": "conv_12345"
            }
        }


class MemorySearchRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="搜索关键词")
    device_id: Optional[str] = Field(default=None, description="设备编号过滤")
    device_name: Optional[str] = Field(default=None, description="设备名称过滤")
    error_code: Optional[str] = Field(default=None, description="故障码过滤")
    top_k: int = Field(default=5, ge=1, le=20, description="返回数量")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "充电中断电",
                "device_id": "IEVC-3.0-001",
                "error_code": "E001",
                "top_k": 5
            }
        }


class MemoryResponse(BaseModel):
    """记忆条目"""
    id: int
    device_id: str
    device_name: Optional[str]
    error_code: Optional[str]
    symptoms: str
    solution: Optional[str]
    primary_cause: Optional[str]
    hit_count: int
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "device_id": "IEVC-3.0-001",
                "device_name": "1 号充电桩",
                "error_code": "E001",
                "symptoms": "充电时突然断电",
                "solution": "检查充电模块保险丝",
                "primary_cause": "保险丝熔断",
                "hit_count": 15,
                "created_at": "2026-05-20T10:00:00"
            }
        }


class MemorySearchResponse(BaseModel):
    """检索响应"""
    cases: list[MemoryResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "cases": [
                    {
                        "id": 1,
                        "device_id": "IEVC-3.0-001",
                        "device_name": "1 号充电桩",
                        "error_code": "E001",
                        "symptoms": "充电时突然断电",
                        "solution": "检查充电模块保险丝",
                        "primary_cause": "保险丝熔断",
                        "hit_count": 15,
                        "created_at": "2026-05-20T10:00:00"
                    }
                ],
                "total": 1
            }
        }
