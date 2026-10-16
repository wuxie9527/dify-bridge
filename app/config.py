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
    log_dir: str = "logs"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 应用
    app_name: str = "Dify Bridge"
    app_version: str = "1.0.0"

    # 阿里云 OCR (新版 SDK)
    alibaba_cloud_access_key_id: str = ""
    alibaba_cloud_access_key_secret: str = ""
    aliyun_ocr_endpoint: str = "ocr-api.cn-hangzhou.aliyuncs.com"

    # Tavily API（备用）
    tavily_api_key: str = ""

    # Tair 云数据库（向量缓存）
    tair_host: str = ""
    tair_port: int = 6379
    tair_password: str = ""
    tair_vector_index: str = "diagnosis_cache"  # TairVector 索引名
    tair_socket_timeout: float = 5.0

    # 阿里云百炼 DashScope（用户提问向量化）
    dashscope_api_key: str = ""
    embedding_model: str = "text-embedding-v3"
    embedding_dimension: int = 1024  # 注意：与索引维度一致，修改需重建索引

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
