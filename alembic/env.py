from logging.config import fileConfig
import asyncio
from sqlalchemy import pool
from alembic import context

# 导入项目配置和模型
from app.config import get_settings
from app.db.database import Base
from app.db import models  # 导入所有模型，确保能被 alembic 检测到

settings = get_settings()

# this is the Alembic Config object
config = context.config

# 设置目标元数据（用于 autogenerate）
target_metadata = Base.metadata

# 使用项目配置中的数据库 URL
sqlalchemy_url = settings.database_url


def run_migrations_offline() -> None:
    """离线模式执行迁移"""
    context.configure(
        url=sqlalchemy_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """执行迁移"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # SQLite 需要
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """异步模式执行迁移"""
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        sqlalchemy_url,
        poolclass=pool.NullPool,
        future=True,
    )

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    """在线模式执行迁移"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
