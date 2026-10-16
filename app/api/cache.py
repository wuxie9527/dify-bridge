"""
向量缓存 API 接口

提供设备诊断缓存的写入与语义检索:
- 写入:设备名称/设备ID/错误码/用户提问/维修方案,用户提问经向量化后存入 TairVector
- 检索:先按设备 ID 与错误码精确过滤,剩余记录按用户提问语义相似度排序
"""
import logging
from typing import Dict

from fastapi import APIRouter, HTTPException
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.clients.dashscope_embedding import EmbeddingError
from app.schemas.cache import (
    CacheCreate,
    CacheCreateResponse,
    CacheItem,
    CacheSearchRequest,
    CacheSearchResponse,
)
from app.services import cache_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cache", tags=["向量缓存"])


def _handle_store_error(e: Exception, action: str) -> HTTPException:
    """将底层异常映射为合适的 HTTP 错误"""
    if isinstance(e, (RedisConnectionError, RedisTimeoutError, ConnectionError)):
        return HTTPException(status_code=503, detail=f"向量存储连接失败: {e}")
    logger.exception(f"{action}失败")
    return HTTPException(status_code=500, detail=f"{action}失败: {e}")


@router.post(
    "",
    summary="写入缓存",
    description=(
        "诊断完成后调用,将设备名称、设备ID、错误码、用户提问、维修方案存入向量缓存。"
        "用户提问会先经 DashScope 向量化。同一设备+错误码+提问重复写入时覆盖更新。"
    ),
    response_model=CacheCreateResponse,
)
async def create_cache(data: CacheCreate) -> CacheCreateResponse:
    """写入缓存(用户提问向量化后存入)"""
    try:
        result = await cache_service.create_cache(data)
        return CacheCreateResponse(**result)
    except EmbeddingError as e:
        raise HTTPException(status_code=503, detail=f"向量化服务不可用: {e}") from e
    except Exception as e:  # noqa: BLE001
        raise _handle_store_error(e, "写入缓存") from e


@router.post(
    "/search",
    summary="语义检索缓存",
    description=(
        "查询时先用设备 ID 和错误码精确过滤,再对剩余记录按用户提问做语义检索,"
        "返回按相似度降序的历史维修方案。"
        "默认 max_distance=1.0(相似度≈0.5),低于阈值的不相关结果自动过滤,"
        "传 max_distance=2.0 可近似关闭阈值。"
    ),
    response_model=CacheSearchResponse,
)
async def search_cache(request: CacheSearchRequest) -> CacheSearchResponse:
    """先精确过滤(设备ID/错误码),再语义检索(用户提问)"""
    try:
        results = await cache_service.search_cache(request)
        return CacheSearchResponse(
            results=[CacheItem(**item) for item in results],
            total=len(results),
        )
    except EmbeddingError as e:
        raise HTTPException(status_code=503, detail=f"向量化服务不可用: {e}") from e
    except Exception as e:  # noqa: BLE001
        raise _handle_store_error(e, "缓存检索") from e


@router.delete(
    "/{key}",
    summary="删除缓存记录",
    description="按写入时返回的 key(md5)删除指定缓存记录",
    responses={
        200: {"description": "删除成功", "example": {"status": "success", "key": "e80b5017098950fc58ead83c8c7ce77c"}},
        404: {"description": "记录不存在"},
    },
)
async def delete_cache(key: str) -> Dict[str, str]:
    """删除缓存记录"""
    deleted = await cache_service.delete_cache(key)
    if not deleted:
        raise HTTPException(status_code=404, detail="缓存记录不存在")
    return {"status": "success", "key": key}
