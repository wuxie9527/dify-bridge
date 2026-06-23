"""
阿里云 OCR 客户端 - 新版 SDK (20210707 版本)
按照阿里云官方文档编写
"""
import logging
from typing import Optional, Dict, Any
import os

from alibabacloud_ocr_api20210707.client import Client
from alibabacloud_ocr_api20210707.models import (
    RecognizeAllTextRequest,
    RecognizeVehicleLicenseRequest,
    RecognizeDrivingLicenseRequest,
)
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions

logger = logging.getLogger(__name__)


class AliyunOCRClient:
    """阿里云 OCR 客户端 - 新版 SDK"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str = "ocr-api.cn-hangzhou.aliyuncs.com"
    ):
        """
        初始化客户端

        Args:
            access_key_id: 阿里云 AccessKey ID
            access_key_secret: 阿里云 AccessKey Secret
            endpoint: OCR API endpoint，默认 "ocr-api.cn-hangzhou.aliyuncs.com"
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint

        # 配置客户端
        config = Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint
        )

        self.client = Client(config)
        logger.info(f"AliyunOCRClient initialized: endpoint={endpoint}")

    def recognize_general(self, image_url: Optional[str] = None, image_base64: Optional[str] = None) -> Dict[str, Any]:
        """
        通用文字识别（统一识别接口）

        Args:
            image_url: 图片 URL（可选）
            image_base64: 图片 Base64 编码（可选，与 image_url 二选一）

        Returns:
            {
                "success": True,
                "data": {
                    "text": "识别的完整文本",
                    "lines": [...]
                },
                "error": None
            }
        """
        try:
            # 统一识别接口，Type 参数指定图片类型
            # General: 通用文字识别基础版（首字母大写）
            request = RecognizeAllTextRequest(
                url=image_url,
                type="General"  # 通用文字识别基础版
            )

            runtime = RuntimeOptions()
            response = self.client.recognize_all_text_with_options(request, runtime)

            # SDK 返回结构：response.body.code/data/message/request_id
            body = response.body
            if body.code:  # code 不为空表示有错误
                return {
                    "success": False,
                    "data": None,
                    "error": f"{body.code}: {body.message}"
                }

            # 解析响应 - data 是 RecognizeAllTextResponseBodyData 对象
            data = body.data
            all_text = getattr(data, "content", "")

            # 从 sub_images 中解析文字块信息
            sub_images = getattr(data, "sub_images", []) or []
            parsed_lines = []

            for sub_img in sub_images:
                if isinstance(sub_img, dict):
                    block_info = sub_img.get("block_info", {})
                    block_details = block_info.get("block_details", []) if isinstance(block_info, dict) else []
                    for block in block_details:
                        if isinstance(block, dict):
                            parsed_lines.append({
                                "text": block.get("block_content", ""),
                                "confidence": block.get("block_confidence", 0) / 100.0,
                                "bbox": block.get("block_points", [])
                            })
                else:
                    # 对象方式访问
                    block_info = getattr(sub_img, "block_info", None)
                    if block_info:
                        block_details = getattr(block_info, "block_details", []) or []
                        for block in block_details:
                            if isinstance(block, dict):
                                parsed_lines.append({
                                    "text": block.get("block_content", ""),
                                    "confidence": block.get("block_confidence", 0) / 100.0,
                                    "bbox": block.get("block_points", [])
                                })
                            else:
                                parsed_lines.append({
                                    "text": getattr(block, "block_content", ""),
                                    "confidence": getattr(block, "block_confidence", 0) / 100.0,
                                    "bbox": getattr(block, "block_points", [])
                                })

            return {
                "success": True,
                "data": {
                    "text": all_text,
                    "lines": parsed_lines,
                    "full_response": {
                        "content": all_text,
                        "sub_image_count": getattr(data, "sub_image_count", 0),
                        "width": getattr(data, "width", 0),
                        "height": getattr(data, "height", 0)
                    }
                },
                "error": None
            }

        except Exception as e:
            logger.error(f"Error in recognize_general: {e}")
            return {"success": False, "data": None, "error": str(e)}

    def recognize_vehicle_license(self, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        行驶证识别

        Args:
            image_url: 行驶证图片 URL

        Returns:
            {
                "success": True,
                "data": {
                    "plate_number": "京 A12345",
                    "vehicle_type": "小型轿车",
                    ...
                }
            }
        """
        try:
            request = RecognizeVehicleLicenseRequest(url=image_url)
            runtime = RuntimeOptions()
            response = self.client.recognize_vehicle_license_with_options(request, runtime)
            result = response.body

            if not result.success:
                return {
                    "success": False,
                    "data": None,
                    "error": f"{result.code}: {result.message}"
                }

            data = result.data
            return {
                "success": True,
                "data": {
                    "plate_number": data.get("plateNumber", ""),
                    "vehicle_type": data.get("vehicleType", ""),
                    "owner": data.get("owner", ""),
                    "use_character": data.get("useCharacter", ""),
                    "model": data.get("model", ""),
                    "vin": data.get("vin", ""),
                    "engine_number": data.get("engineNumber", ""),
                    "register_date": data.get("registerDate", ""),
                    "issue_date": data.get("issueDate", ""),
                    "full_response": data
                },
                "error": None
            }

        except Exception as e:
            logger.error(f"Error in recognize_vehicle_license: {e}")
            return {"success": False, "data": None, "error": str(e)}

    def recognize_driving_license(self, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        驾驶证识别

        Args:
            image_url: 驾驶证图片 URL

        Returns:
            {
                "success": True,
                "data": {
                    "name": "张三",
                    "sex": "男",
                    ...
                }
            }
        """
        try:
            request = RecognizeDrivingLicenseRequest(url=image_url)
            runtime = RuntimeOptions()
            response = self.client.recognize_driving_license_with_options(request, runtime)
            result = response.body

            if not result.success:
                return {
                    "success": False,
                    "data": None,
                    "error": f"{result.code}: {result.message}"
                }

            data = result.data
            return {
                "success": True,
                "data": {
                    "name": data.get("name", ""),
                    "sex": data.get("sex", ""),
                    "class": data.get("class", ""),
                    "license_number": data.get("licenseNumber", ""),
                    "issue_date": data.get("issueDate", ""),
                    "expiry_date": data.get("expiryDate", ""),
                    "full_response": data
                },
                "error": None
            }

        except Exception as e:
            logger.error(f"Error in recognize_driving_license: {e}")
            return {"success": False, "data": None, "error": str(e)}


# 全局客户端实例
_ocr_client: Optional[AliyunOCRClient] = None


def get_ocr_client() -> Optional[AliyunOCRClient]:
    """获取 OCR 客户端实例"""
    return _ocr_client


def init_ocr_client(
    access_key_id: str,
    access_key_secret: str,
    endpoint: str = "ocr-api.cn-hangzhou.aliyuncs.com"
) -> AliyunOCRClient:
    """初始化 OCR 客户端"""
    global _ocr_client
    _ocr_client = AliyunOCRClient(access_key_id, access_key_secret, endpoint)
    return _ocr_client