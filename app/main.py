"""
Dify Bridge - 简化版
只保留核心功能：长期记忆、OCR、Excel 审核
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.api import memory_router
from app.api.ocr_router import router as ocr_router
from app.api.report_router import router as report_router

# 配置日志
settings = get_settings()
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), settings.log_dir)
os.makedirs(log_dir, exist_ok=True)

# 创建日志处理器
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, "app.log"),
    when="D",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(settings.log_format))
file_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(settings.log_format))
console_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

# 配置根日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 50)
    logger.info("Starting Dify Bridge service...")
    logger.info(f"Version: {settings.app_version}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Log dir: {log_dir}")

    # 初始化数据库
    await init_db()
    logger.info("Database initialized")

    # 初始化 OCR 客户端
    if settings.alibaba_cloud_access_key_id and settings.alibaba_cloud_access_key_secret:
        from app.clients.aliyun_ocr import init_ocr_client
        init_ocr_client(
            access_key_id=settings.alibaba_cloud_access_key_id,
            access_key_secret=settings.alibaba_cloud_access_key_secret,
            endpoint=settings.aliyun_ocr_endpoint
        )
        logger.info(f"Aliyun OCR client initialized: endpoint={settings.aliyun_ocr_endpoint}")
    else:
        logger.warning("Aliyun OCR credentials not configured")

    # 确保数据目录存在
    data_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "outputs")
    ]
    for dir_path in data_dirs:
        os.makedirs(dir_path, exist_ok=True)
    logger.info("Data directories initialized")

    logger.info("Application startup complete")
    logger.info("=" * 50)

    yield

    logger.info("Service shutting down...")


app = FastAPI(
    title="Dify Bridge",
    description="资产评估报告审核后端服务",
    version=settings.app_version,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(memory_router, prefix="/api/v1/dify", tags=["长期记忆"])
app.include_router(ocr_router, tags=["OCR 识别"])
app.include_router(report_router, tags=["报告审核"])


@app.get("/", tags=["健康检查"])
async def root():
    """健康检查"""
    return {"status": "ok", "service": "dify-bridge"}


@app.get("/health", tags=["健康检查"])
async def health_check():
    """详细健康检查"""
    return {
        "status": "ok",
        "service": "dify-bridge",
        "version": settings.app_version,
        "features": ["长期记忆", "OCR 识别", "Excel 提取", "Excel 批注写回", "Word 批注写回"],
        "log_dir": log_dir
    }
