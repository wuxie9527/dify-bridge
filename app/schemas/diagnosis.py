"""
诊断相关 Schema
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DeviceUpdateInput(BaseModel):
    """设备更新输入"""
    model: Optional[str] = Field(default=None, description="型号，如 IEVC-3.0")
    common_faults: Optional[list] = Field(default=None, description="常见故障 Top3")
    last_maintenance_date: Optional[str] = Field(default=None, description="上次保养日期")
    notes: Optional[str] = Field(default=None, description="备注")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "IEVC-3.0",
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
