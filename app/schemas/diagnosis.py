"""
诊断相关 Schema
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


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
    query: Optional[str] = Field(default=None, description="搜索关键词")
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
