"""
Dify Bridge - 配置管理
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 数据库
    database_url: str = "sqlite+aiosqlite:///data/battery.db"

    # 日志
    log_level: str = "INFO"

    # 应用
    app_name: str = "Dify Bridge"
    app_version: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
