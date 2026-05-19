"""
Dify Bridge - Dify 服务中台
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.api import dify_tools

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
app.include_router(dify_tools.router, prefix="/api/v1/dify", tags=["Dify Tools"])


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
