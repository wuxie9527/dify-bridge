"""
DashScope Embedding 客户端 - 用户提问向量化

使用阿里云百炼 OpenAI 兼容接口,无需额外 SDK 依赖。
文档: https://help.aliyun.com/zh/model-studio/text-embedding-api
"""
import logging
from typing import List

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
BATCH_SIZE = 10  # DashScope Embedding 每次请求最多 10 条文本


class EmbeddingError(Exception):
    """向量化失败"""


class DashScopeEmbeddingClient:
    """DashScope 文本向量化客户端(OpenAI 兼容模式)"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.dashscope_api_key
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self.timeout = 30.0

    @property
    def configured(self) -> bool:
        """是否已配置 API Key"""
        return bool(self.api_key)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """将一批文本转为向量(自动分批)

        Args:
            texts: 文本列表

        Returns:
            与输入顺序一致的向量列表

        Raises:
            EmbeddingError: 未配置 Key 或 API 调用失败
        """
        if not self.configured:
            raise EmbeddingError("DASHSCOPE_API_KEY 未配置,无法向量化")
        if not texts:
            return []

        vectors: List[List[float]] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for start in range(0, len(texts), BATCH_SIZE):
                batch = texts[start:start + BATCH_SIZE]
                vectors.extend(await self._embed_batch(client, batch))
        return vectors

    async def embed_one(self, text: str) -> List[float]:
        """单条文本向量化"""
        return (await self.embed([text]))[0]

    async def _embed_batch(self, client: httpx.AsyncClient, batch: List[str]) -> List[List[float]]:
        payload = {
            "model": self.model,
            "input": batch,
            "dimensions": self.dimension,
            "encoding_format": "float",
        }
        try:
            response = await client.post(
                f"{DASHSCOPE_BASE_URL}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            body = ""
            if hasattr(e, "response") and e.response is not None:
                body = e.response.text[:500]
            logger.error(f"DashScope Embedding 请求失败: {e} {body}")
            raise EmbeddingError(f"DashScope Embedding 请求失败: {e}") from e

        data = response.json()
        try:
            # 按 index 排序,确保与输入顺序一致
            items = sorted(data["data"], key=lambda x: x["index"])
            vectors = [item["embedding"] for item in items]
        except (KeyError, TypeError) as e:
            logger.error(f"DashScope Embedding 响应格式异常: {data}")
            raise EmbeddingError("DashScope Embedding 响应格式异常") from e

        if len(vectors) != len(batch):
            raise EmbeddingError(f"Embedding 返回数量({len(vectors)})与输入({len(batch)})不一致")
        return vectors
