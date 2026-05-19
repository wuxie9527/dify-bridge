"""
Schema 模块 - Pydantic 数据模型
"""
from app.schemas.diagnosis import (
    SimilarCaseQuery,
    SolutionRecord,
)

__all__ = [
    "SimilarCaseQuery",
    "SolutionRecord",
]
