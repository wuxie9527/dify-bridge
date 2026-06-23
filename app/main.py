"""
Dify Bridge - Dify 服务中台
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.api import memory_router
from app.api.ocr_router import router as ocr_router
from app.clients.aliyun_ocr import init_ocr_client

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Dify Bridge service...")
    await init_db()
    logger.info("Database initialized")

    # 初始化 OCR 客户端
    settings = get_settings()
    if settings.alibaba_cloud_access_key_id and settings.alibaba_cloud_access_key_secret:
        init_ocr_client(
            access_key_id=settings.alibaba_cloud_access_key_id,
            access_key_secret=settings.alibaba_cloud_access_key_secret,
            endpoint=settings.aliyun_ocr_endpoint
        )
        logger.info(f"Aliyun OCR client initialized: endpoint={settings.aliyun_ocr_endpoint}")
    else:
        logger.warning("Aliyun OCR credentials not configured, OCR features will be unavailable")

    yield
    logger.info("Service shutting down...")


app = FastAPI(
    title="Dify Bridge",
    description="为 Dify Agent 提供数据服务和能力封装的中转平台",
    version=get_settings().app_version,
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
        "version": get_settings().app_version
    }
