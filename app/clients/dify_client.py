"""
Dify API 客户端 - 封装 Dify Open API
"""
import logging
import httpx
from typing import Dict, Any, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DifyClient:
    """Dify API 客户端"""

    def __init__(self):
        self.base_url = settings.dify_api_url.rstrip("/")
        self.api_key = settings.dify_api_key
        self.timeout = 30.0

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def start_conversation(
        self,
        user_id: str,
        query: str,
        inputs: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        启动或继续对话

        Args:
            user_id: 用户 ID
            query: 用户输入
            inputs: 会话变量（如 diagnosis_state）
            conversation_id: 已有会话 ID（可选）

        Returns:
            Dify 响应数据
        """
        payload = {
            "user": user_id,
            "query": query,
            "inputs": inputs or {},
            "response_mode": "blocking"  # 阻塞模式，等待完整响应
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat-messages",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Dify API 请求失败：{e}")
            raise

    async def send_message(
        self,
        conversation_id: str,
        user_id: str,
        message: str,
        inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送消息到已有会话

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID
            message: 消息内容
            inputs: 更新的会话变量

        Returns:
            Dify 响应数据
        """
        return await self.start_conversation(
            user_id=user_id,
            query=message,
            inputs=inputs,
            conversation_id=conversation_id
        )

    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取会话历史消息

        Args:
            conversation_id: 会话 ID
            user_id: 用户 ID
            limit: 消息数量限制

        Returns:
            消息列表
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/messages",
                    headers=self._get_headers(),
                    params={
                        "conversation_id": conversation_id,
                        "user": user_id,
                        "limit": limit
                    }
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Dify API 请求失败：{e}")
            raise

    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        执行 Workflow

        Args:
            workflow_id: 工作流 ID
            inputs: 输入参数
            user_id: 用户 ID

        Returns:
            执行结果
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/workflows/run",
                    headers=self._get_headers(),
                    json={
                        "inputs": inputs,
                        "user": user_id,
                        "response_mode": "blocking"
                    }
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Dify Workflow 请求失败：{e}")
            raise
