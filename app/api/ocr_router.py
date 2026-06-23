"""
OCR 识别 API 路由
提供图片文字识别、证件识别等接口
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.clients.aliyun_ocr_new import get_ocr_client

router = APIRouter(prefix="/api/v1/ocr", tags=["OCR 识别"])


class OCRRequest(BaseModel):
    """OCR 请求模型"""
    image_url: Optional[str] = Field(None, description="图片 URL")
    image_base64: Optional[str] = Field(None, description="图片 Base64 编码")
    mode: str = Field("general", description="识别模式：general(通用), vehicle_license(行驶证), driving_license(驾驶证)")


class OCRResponse(BaseModel):
    """OCR 响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/recognize", response_model=OCRResponse, summary="OCR 识别")
async def recognize(request: OCRRequest):
    """
    OCR 文字识别接口

    ### 支持类型:
    - **general**: 通用文字识别
    - **vehicle_license**: 行驶证识别
    - **driving_license**: 驾驶证识别

    ### 请求参数:
    - `image_url`: 图片公网 URL（可选）
    - `image_base64`: 图片 Base64 编码（可选，与 image_url 二选一）
    - `mode`: 识别模式

    ### 返回示例:
    ```json
    {
        "success": true,
        "data": {
            "text": "识别的文本内容",
            "lines": [
                {"text": "第一行", "confidence": 0.98, "bbox": [...]}
            ]
        },
        "error": null
    }
    ```
    """
    client = get_ocr_client()
    if not client:
        raise HTTPException(status_code=500, detail="OCR 客户端未初始化，请检查配置")

    if not request.image_url and not request.image_base64:
        raise HTTPException(status_code=400, detail="必须提供 image_url 或 image_base64")

    # 根据模式选择识别方法
    if request.mode == "general":
        result = client.recognize_general(
            image_url=request.image_url,
            image_base64=request.image_base64
        )
    elif request.mode == "vehicle_license":
        result = client.recognize_vehicle_license(
            image_url=request.image_url,
            image_base64=request.image_base64
        )
    elif request.mode == "driving_license":
        result = client.recognize_driving_license(
            image_url=request.image_url,
            image_base64=request.image_base64
        )
    else:
        raise HTTPException(status_code=400, detail=f"不支持的识别模式：{request.mode}")

    return OCRResponse(**result)


@router.post("/recognize/general", response_model=OCRResponse, summary="通用文字识别")
async def recognize_general(
    image_url: Optional[str] = Body(None, description="图片 URL"),
    image_base64: Optional[str] = Body(None, description="图片 Base64 编码")
):
    """
    通用文字识别 - 简化接口

    适用于文档、票据、名片等各种场景的文字识别
    """
    client = get_ocr_client()
    if not client:
        raise HTTPException(status_code=500, detail="OCR 客户端未初始化")

    if not image_url and not image_base64:
        raise HTTPException(status_code=400, detail="必须提供 image_url 或 image_base64")

    result = client.recognize_general(image_url=image_url, image_base64=image_base64)
    return OCRResponse(**result)


@router.post("/recognize/vehicle-license", response_model=OCRResponse, summary="行驶证识别")
async def recognize_vehicle_license(
    image_url: Optional[str] = Body(None, description="行驶证图片 URL"),
    image_base64: Optional[str] = Body(None, description="行驶证图片 Base64")
):
    """
    行驶证识别

    自动提取：车牌号、车辆类型、所有人、使用性质、品牌型号、VIN 码、发动机号、注册日期等
    """
    client = get_ocr_client()
    if not client:
        raise HTTPException(status_code=500, detail="OCR 客户端未初始化")

    if not image_url and not image_base64:
        raise HTTPException(status_code=400, detail="必须提供 image_url 或 image_base64")

    result = client.recognize_vehicle_license(image_url=image_url, image_base64=image_base64)
    return OCRResponse(**result)


@router.post("/recognize/driving_license", response_model=OCRResponse, summary="驾驶证识别")
async def recognize_driving_license(
    image_url: Optional[str] = Body(None, description="驾驶证图片 URL"),
    image_base64: Optional[str] = Body(None, description="驾驶证图片 Base64")
):
    """
    驾驶证识别

    自动提取：姓名、性别、国籍、住址、出生日期、初次领证日期、有效期限、证号、准驾车型等
    """
    client = get_ocr_client()
    if not client:
        raise HTTPException(status_code=500, detail="OCR 客户端未初始化")

    if not image_url and not image_base64:
        raise HTTPException(status_code=400, detail="必须提供 image_url 或 image_base64")

    result = client.recognize_driving_license(image_url=image_url, image_base64=image_base64)
    return OCRResponse(**result)


@router.get("/test", tags=["健康检查"])
async def test_ocr():
    """测试 OCR 服务状态"""
    client = get_ocr_client()
    if client:
        return {"status": "connected", "endpoint": client.endpoint}
    else:
        return {"status": "not_initialized", "message": "OCR 客户端未初始化"}
