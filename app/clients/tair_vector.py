"""
TairVector 向量存储客户端 - 诊断缓存的向量检索

基于阿里云 Tair 的 TairVector 模块实现:
- HNSW 索引 + L2 距离
- device_id / error_code 建标量倒排索引,支持前置过滤(PreFilter):
  先精确过滤,再对剩余数据做向量语义检索
- filter 表达式语法(官方要求):操作符 == 、&&,字符串用双引号,操作符两侧必须有空格

注意:pytair SDK 为同步客户端,本类只提供同步方法,
由上层服务通过 asyncio.to_thread 包装调用,避免阻塞事件循环。
"""
import hashlib
import logging
import time
from typing import Any, Dict, List, Optional, Sequence

import tair

from app.config import get_settings

logger = logging.getLogger(__name__)

# TairVector 索引中存储的标量字段
FIELDS = ("device_id", "device_name", "error_code", "question", "solution", "created_at")


def _escape(value: str) -> str:
    """转义 filter 表达式中的字符串值(仅保留安全字符语义)"""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_filter(device_id: Optional[str], error_code: Optional[str]) -> Optional[str]:
    """构造标量过滤表达式,如:device_id == "x" && error_code == "y\""""
    conditions = []
    if device_id:
        conditions.append(f'device_id == "{_escape(device_id)}"')
    if error_code:
        conditions.append(f'error_code == "{_escape(error_code)}"')
    return " && ".join(conditions) if conditions else None


def build_key(device_id: str, error_code: str, question: str) -> str:
    """记录 key:同设备+同错误码+同提问自然去重(重复写入即覆盖更新)"""
    raw = f"{device_id}|{error_code}|{question}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


class TairVectorStore:
    """TairVector 向量存储(同步客户端)"""

    def __init__(self):
        self._client: Optional[tair.Tair] = None

    @property
    def client(self) -> tair.Tair:
        """懒加载连接(自带连接池)"""
        if self._client is None:
            settings = get_settings()
            if not settings.tair_host:
                raise ConnectionError("TAIR_HOST 未配置,无法连接向量存储")
            self._client = tair.Tair(
                host=settings.tair_host,
                port=settings.tair_port,
                password=settings.tair_password or None,
                socket_connect_timeout=settings.tair_socket_timeout,
                socket_timeout=settings.tair_socket_timeout,
            )
        return self._client

    def close(self):
        """关闭连接"""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:  # noqa: BLE001
                pass
            self._client = None

    def ensure_index(self) -> bool:
        """确保向量索引存在,不存在则创建(幂等)

        创建时声明 device_id / error_code 的标量倒排索引,
        使检索支持前置过滤(search_policy scala)。
        """
        settings = get_settings()
        index_name = settings.tair_vector_index
        client = self.client

        try:
            client.tvs_create_index(
                index_name,
                settings.embedding_dimension,
                distance_type="L2",
                index_type="HNSW",
                inverted_index_device_id="string",
                inverted_index_error_code="string",
            )
            logger.info(f"TairVector 索引已创建: {index_name} (dim={settings.embedding_dimension})")
            return True
        except tair.exceptions.ResponseError as e:
            if "exist" in str(e).lower():
                logger.info(f"TairVector 索引已存在: {index_name}")
                return True
            # 部分低版本内核不支持倒排索引声明,降级为普通索引(检索退化为后置过滤)
            logger.warning(f"创建带倒排索引的向量索引失败({e}),尝试创建普通索引")
            try:
                client.tvs_create_index(
                    index_name,
                    settings.embedding_dimension,
                    distance_type="L2",
                    index_type="HNSW",
                )
                logger.info(f"TairVector 普通索引已创建: {index_name}")
                return True
            except tair.exceptions.ResponseError as e2:
                if "exist" in str(e2).lower():
                    return True
                raise

    def upsert(
        self,
        vector: Sequence[float],
        device_id: str,
        question: str,
        device_name: str = "",
        error_code: str = "",
        solution: str = "",
    ) -> str:
        """写入/更新一条缓存记录(同 key 覆盖)

        Returns:
            记录 key(md5)
        """
        key = build_key(device_id, error_code, question)
        self.client.tvs_hset(
            get_settings().tair_vector_index,
            key,
            list(vector),
            device_id=device_id,
            device_name=device_name or "",
            error_code=error_code or "",
            question=question,
            solution=solution or "",
            created_at=str(int(time.time())),
        )
        return key

    def search(
        self,
        vector: Sequence[float],
        top_k: int = 5,
        device_id: Optional[str] = None,
        error_code: Optional[str] = None,
        max_distance: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """向量近邻检索,可先按 device_id / error_code 精确过滤(前置过滤)

        Args:
            vector: 查询向量
            top_k: 返回数量
            device_id: 设备编号精确过滤(可选)
            error_code: 错误码精确过滤(可选)
            max_distance: 距离阈值,超过则丢弃(可选;L2 距离,归一化向量下
                          0=完全相同,约1.0≈余弦相似度0.5)

        Returns:
            按 distance 升序的结果列表,含 key / distance / similarity 及全部字段
        """
        index_name = get_settings().tair_vector_index
        filter_str = build_filter(device_id, error_code)

        kwargs: Dict[str, Any] = {}
        if filter_str:
            kwargs["filter_str"] = filter_str
            kwargs["search_policy"] = "scala"  # 前置过滤:先标量精确过滤,再向量检索

        results = self.client.tvs_knnsearch(index_name, top_k, list(vector), **kwargs)
        if not results:
            return []

        items: List[Dict[str, Any]] = []
        for key, distance in results:
            key_str = key.decode() if isinstance(key, bytes) else str(key)
            if max_distance is not None and distance > max_distance:
                continue
            fields = self.get_fields(key_str)
            item = {
                "key": key_str,
                "distance": round(float(distance), 6),
                # 归一化向量 + L2 距离 => 余弦相似度 = 1 - d²/2
                "similarity": round(max(0.0, 1.0 - float(distance) ** 2 / 2), 6),
            }
            item.update(fields)
            items.append(item)
        return items

    def exists(self, key: str) -> bool:
        """判断记录是否存在"""
        raw = self.client.tvs_hgetall(get_settings().tair_vector_index, key)
        return bool(raw)

    def get_fields(self, key: str) -> Dict[str, str]:
        """读取记录的全部标量字段(不存在的记录返回全空字段)"""
        raw = self.client.tvs_hgetall(get_settings().tair_vector_index, key)
        decoded = {}
        if raw:
            for k, v in raw.items():
                k_str = k.decode() if isinstance(k, bytes) else str(k)
                v_str = v.decode() if isinstance(v, bytes) else str(v)
                decoded[k_str] = v_str
        # 补齐缺失字段
        return {f: decoded.get(f, "") for f in FIELDS}

    def delete(self, key: str) -> bool:
        """删除一条记录"""
        return bool(self.client.tvs_del(get_settings().tair_vector_index, key))


# 模块级单例
_vector_store: Optional[TairVectorStore] = None


def get_vector_store() -> TairVectorStore:
    """获取向量存储单例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = TairVectorStore()
    return _vector_store
