"""
向量缓存服务 - 组合 Embedding 向量化与 TairVector 检索

写入流程:用户提问 -> DashScope 向量化 -> TairVector 存储(同 key 覆盖)
检索流程:查询文本 -> 向量化 -> 按设备 ID/错误码前置精确过滤 -> 语义近邻检索
"""
import asyncio
import logging
from typing import Any, Dict, List

from app.clients.dashscope_embedding import DashScopeEmbeddingClient
from app.clients.tair_vector import get_vector_store, build_key
from app.schemas.cache import CacheCreate, CacheSearchRequest

logger = logging.getLogger(__name__)

# 复用单例客户端
_embedding_client = DashScopeEmbeddingClient()


async def create_cache(data: CacheCreate) -> Dict[str, Any]:
    """写入缓存:用户提问向量化后存入 TairVector

    Returns:
        {"status": "success", "key": md5, "is_update": bool}
    """
    store = get_vector_store()

    # 同设备+同错误码+同提问 => 同 key,重复写入即覆盖更新
    key = build_key(data.device_id, data.error_code or "", data.question)
    existed = await asyncio.to_thread(store.exists, key)

    # 向量化(异步 HTTP 调用)
    vector = await _embedding_client.embed_one(data.question)

    # 写入(同步 SDK,放入线程池执行)
    await asyncio.to_thread(
        store.upsert,
        vector,
        device_id=data.device_id,
        question=data.question,
        device_name=data.device_name or "",
        error_code=data.error_code or "",
        solution=data.solution or "",
    )
    logger.info(
        f"缓存已{'更新' if existed else '写入'}: key={key} device_id={data.device_id} "
        f"error_code={data.error_code}"
    )
    return {"status": "success", "key": key, "is_update": existed}


async def search_cache(request: CacheSearchRequest) -> List[Dict[str, Any]]:
    """语义检索:先按设备 ID/错误码精确过滤,再按提问语义检索

    Returns:
        按相似度降序的结果字典列表
    """
    store = get_vector_store()

    # 查询文本向量化
    vector = await _embedding_client.embed_one(request.query)

    # 前置过滤 + KNN 语义检索(同步 SDK,放入线程池执行)
    results = await asyncio.to_thread(
        store.search,
        vector,
        top_k=request.top_k,
        device_id=request.device_id,
        error_code=request.error_code,
        max_distance=request.max_distance,
    )
    logger.info(
        f"缓存检索: query={request.query!r} device_id={request.device_id} "
        f"error_code={request.error_code} 命中 {len(results)} 条"
    )
    return results


async def delete_cache(key: str) -> bool:
    """删除缓存记录"""
    store = get_vector_store()
    return bool(await asyncio.to_thread(store.delete, key))


async def check_ready() -> Dict[str, Any]:
    """启动时检查依赖是否就绪(用于 lifespan)"""
    status: Dict[str, Any] = {"embedding": False, "vector_store": False}

    if not _embedding_client.configured:
        logger.warning("DASHSCOPE_API_KEY 未配置,缓存写入/检索将不可用")
    else:
        status["embedding"] = True

    try:
        store = get_vector_store()
        from app.config import get_settings
        await asyncio.to_thread(store.ensure_index)
        status["vector_store"] = True
        logger.info(f"TairVector 向量存储就绪: index={get_settings().tair_vector_index}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"TairVector 向量存储初始化失败: {e}")

    return status
