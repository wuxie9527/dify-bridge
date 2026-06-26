"""
API 路由模块
"""
from app.api.memory import router as memory_router
from app.api.ocr_router import router as ocr_router
from app.api.report_router import router as report_router

__all__ = ["memory_router", "ocr_router", "report_router"]
