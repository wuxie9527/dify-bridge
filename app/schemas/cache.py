"""
向量缓存 Schema - 设备诊断缓存的写入与语义检索
"""
from typing import Optional
from pydantic import BaseModel, Field


class CacheCreate(BaseModel):
    """写入缓存 - 诊断完成后调用"""
    device_id: str = Field(..., description="设备 ID")
    device_name: Optional[str] = Field(default=None, description="设备名称")
    error_code: Optional[str] = Field(default=None, description="错误码")
    question: str = Field(..., description="用户提问(将向量化后存入)")
    solution: Optional[str] = Field(default=None, description="维修方案")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "IEVC-3.0-001",
                "device_name": "1 号充电桩",
                "error_code": "E001",
                "question": "充电时突然断电怎么办",
                "solution": "检查充电模块保险丝,更换熔断的保险丝"
            }
        }


class CacheSearchRequest(BaseModel):
    """语义检索请求 - 先按设备 ID / 错误码精确过滤,再按用户提问语义检索"""
    query: str = Field(..., description="用户提问(语义检索的查询文本)")
    device_id: Optional[str] = Field(default=None, description="设备 ID 精确过滤(空字符串等价于不过滤)")
    error_code: Optional[str] = Field(default=None, description="错误码精确过滤(空字符串等价于不过滤)")
    top_k: int = Field(default=5, ge=1, le=20, description="返回数量")
    max_distance: float = Field(
        default=1.0, ge=0,
        description=(
            "距离阈值,L2 距离超过该值的结果将被丢弃(默认 1.0≈相似度 0.5)。"
            "换算: similarity = 1 - distance²/2,如 0.8≈相似度 0.8、1.0≈相似度 0.5;"
            "传 2.0 可近似关闭阈值(归一化向量最大距离约 1.414)"
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "充电过程中老是跳闸",
                "device_id": "IEVC-3.0-001",
                "error_code": "E001",
                "top_k": 5
            }
        }


class CacheItem(BaseModel):
    """缓存条目(检索结果)"""
    key: str = Field(..., description="记录唯一标识(md5),删除时使用")
    device_id: str = Field(..., description="设备 ID")
    device_name: Optional[str] = None
    error_code: Optional[str] = None
    question: str
    solution: Optional[str] = None
    created_at: Optional[int] = Field(default=None, description="写入时间(Unix 时间戳,秒)")
    distance: Optional[float] = Field(default=None, description="向量距离(越小越相似)")
    similarity: Optional[float] = Field(default=None, description="语义相似度(0~1,越大越相似)")


class CacheCreateResponse(BaseModel):
    """写入响应"""
    status: str = "success"
    key: str = Field(..., description="记录唯一标识(md5)")
    is_update: bool = Field(..., description="True=覆盖更新已存在记录,False=新建")


class CacheSearchResponse(BaseModel):
    """检索响应"""
    results: list[CacheItem]
    total: int
