"""
Dify Bridge - 配置管理
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 数据库
    database_url: str = "sqlite+aiosqlite:///data/dify-bridge.db"

    # 日志
    log_level: str = "INFO"

    # 应用
    app_name: str = "Dify Bridge"
    app_version: str = "1.0.0"

    # 阿里云 OCR (新版 SDK)
    alibaba_cloud_access_key_id: str = ""
    alibaba_cloud_access_key_secret: str = ""
    aliyun_ocr_endpoint: str = "ocr-api.cn-hangzhou.aliyuncs.com"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
