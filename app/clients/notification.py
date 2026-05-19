"""
通知客户端 - 短信/邮件/ webhook 通知
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class NotificationClient:
    """通知客户端"""

    def __init__(self):
        self.smtp_server = None  # 从配置读取
        self.smtp_port = None
        self.sender_email = None
        self.sender_password = None

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """
        发送邮件通知

        Args:
            to_emails: 收件人列表
            subject: 邮件主题
            body: 邮件正文
            html: 是否为 HTML 邮件

        Returns:
            是否发送成功
        """
        # 当前版本不实现具体逻辑，返回 False
        # 实际部署时根据需求配置 SMTP 服务器
        logger.warning("邮件通知功能未配置")
        return False

    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        发送 Webhook 通知

        Args:
            url: Webhook URL
            payload: 请求体
            headers: 请求头

        Returns:
            是否发送成功
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers or {"Content-Type": "application/json"}
                )
                response.raise_for_status()
                logger.info(f"Webhook 发送成功：{url}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Webhook 发送失败：{e}")
            return False

    async def notify_error_report(
        self,
        report_id: str,
        device_id: str,
        error_code: str,
        severity: str,
        webhook_url: Optional[str] = None
    ) -> bool:
        """
        发送故障报告通知

        Args:
            report_id: 报告 ID
            device_id: 设备 ID
            error_code: 故障码
            severity: 严重程度
            webhook_url: Webhook URL

        Returns:
            是否发送成功
        """
        payload = {
            "type": "error_report",
            "report_id": report_id,
            "device_id": device_id,
            "error_code": error_code,
            "severity": severity,
            "message": f"设备 {device_id} 上报故障 {error_code}，严重程度：{severity}"
        }

        if webhook_url:
            return await self.send_webhook(webhook_url, payload)

        logger.info(f"故障报告通知：{payload}")
        return True
