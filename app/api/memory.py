"""
长期记忆 API 接口

提供诊断案例的存储和关键词检索功能。
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.repository import MemoryRepository
from app.schemas.diagnosis import (
    MemoryCreate,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory", tags=["长期记忆"])


@router.post(
    "",
    summary="创建或更新诊断记忆",
    description="在 Chatflow 诊断完成后调用，保存本次诊断记录到长期记忆库。如果相同 fault_code 已存在则更新",
    responses={
        200: {
            "description": "创建/更新成功",
            "example": {
                "id": 1,
                "device_id": "IEVC-3.0-001",
                "device_name": "1 号充电桩",
                "error_code": "E001",
                "symptoms": "充电时突然断电",
                "solution": "检查充电模块保险丝",
                "primary_cause": "保险丝熔断",
                "hit_count": 0,
                "created_at": "2026-05-21T12:00:00",
                "is_new": true
            }
        }
    }
)
async def create_memory(
    data: MemoryCreate,
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    创建或更新诊断记忆

    在诊断流程完成后调用，将本次诊断结果保存到长期记忆库。
    如果相同 error_code 已存在则更新，否则新增。
    """
    memory, is_new = await MemoryRepository.create_or_update(session, data.model_dump())
    await session.commit()
    response = MemoryResponse.model_validate(memory).model_dump()
    response["is_new"] = is_new
    return response


@router.post(
    "/search",
    summary="检索长期记忆",
    description="根据关键词检索相似的历史诊断案例，支持设备编号、故障码过滤",
    response_model=MemorySearchResponse,
    responses={
        200: {
            "description": "检索成功",
            "example": {
                "cases": [
                    {
                        "id": 1,
                        "device_id": "IEVC-3.0-001",
                        "device_name": "1 号充电桩",
                        "error_code": "E001",
                        "symptoms": "充电时突然断电",
                        "solution": "检查充电模块保险丝",
                        "primary_cause": "保险丝熔断",
                        "hit_count": 15,
                        "created_at": "2026-05-20T10:00:00"
                    }
                ],
                "total": 1
            }
        }
    }
)
async def search_memory(
    request: MemorySearchRequest,
    session: AsyncSession = Depends(get_db)
) -> MemorySearchResponse:
    """
    检索长期记忆

    在 Chatflow 开始时调用，获取相似历史案例。
    支持关键词匹配、设备编号过滤、故障码过滤。
    返回结果按命中次数和时间倒序排列。
    """
    # 关键词检索
    results = await MemoryRepository.search(
        session,
        query=request.query,
        device_id=request.device_id,
        device_name=request.device_name,
        error_code=request.error_code,
        top_k=request.top_k
    )

    # 增加前 3 个结果的命中次数（异步，不阻塞响应）
    for memory in results[:3]:
        await MemoryRepository.increment_hit_count(session, memory.id)
    await session.commit()

    return MemorySearchResponse(
        cases=[MemoryResponse.model_validate(m) for m in results],
        total=len(results)
    )


@router.get(
    "/{memory_id}",
    summary="根据 ID 获取记忆",
    description="获取单条诊断记忆详情",
    response_model=MemoryResponse,
    responses={
        200: {"description": "获取成功"},
        404: {"description": "记忆不存在"}
    }
)
async def get_memory(
    memory_id: int,
    session: AsyncSession = Depends(get_db)
) -> MemoryResponse:
    """根据 ID 获取记忆"""
    memory = await MemoryRepository.get_by_id(session, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return MemoryResponse.model_validate(memory)


@router.delete(
    "/{memory_id}",
    summary="删除记忆",
    description="删除指定的诊断记忆",
    responses={
        200: {
            "description": "删除成功",
            "example": {"status": "success", "id": 1}
        },
        404: {"description": "记忆不存在"}
    }
)
async def delete_memory(
    memory_id: int,
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """删除记忆"""
    deleted = await MemoryRepository.delete(session, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="记忆不存在")
    await session.commit()
    return {"status": "success", "id": memory_id}
