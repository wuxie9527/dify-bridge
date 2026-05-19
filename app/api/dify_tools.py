"""
Dify 工具接口 - 提供给 Dify 调用的 API

为 Dify Chatflow 提供设备记忆查询、案例检索、解决方案保存等能力。
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.device_manager import DeviceManager
from app.core.case_matcher import CaseMatcher
from app.schemas.diagnosis import SimilarCaseQuery, SolutionRecord, DeviceUpdateInput

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/device/{device_id}",
    summary="查询设备记忆",
    description="根据设备编号查询设备画像信息，包括型号、常见故障 Top3、上次保养日期、备注等",
    tags=["设备记忆"],
    responses={
        200: {
            "description": "查询成功",
            "example": {
                "exists": True,
                "data": {
                    "device_id": "BAT-001",
                    "model": "IEVC-3.0",
                    "device_name": "1 号电池包",
                    "common_faults": ["E001", "E003"],
                    "last_maintenance_date": "2024-01-15T10:00:00",
                    "notes": "需要定期更换冷却液"
                }
            }
        },
        404: {
            "description": "设备不存在",
            "example": {"exists": False, "device_id": "BAT-001"}
        }
    }
)
async def get_device_memory(
    device_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dify 工具：查询设备记忆

    返回设备基本信息、常见故障 Top3、上次保养日期、备注
    """
    return await DeviceManager.get_device(db, device_id)


@router.post(
    "/device/{device_id}/update",
    summary="创建/更新设备记忆",
    description="创建新设备记录或更新现有设备信息，包括型号、常见故障、保养日期、备注等",
    tags=["设备记忆"],
    responses={
        200: {
            "description": "更新成功",
            "example": {
                "status": "success",
                "device_id": "BAT-001",
                "created": True
            }
        }
    }
)
async def update_device(
    device_id: str,
    data: DeviceUpdateInput,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dify 工具：创建或更新设备记忆

    Request Body:
    - model: 型号，如 IEVC-3.0
    - common_faults: 常见故障 Top3 列表，如 ["E001", "E003"]
    - last_maintenance_date: 上次保养日期，ISO 8601 格式
    - notes: 特殊备注
    """
    return await DeviceManager.create_or_update_device(
        db, device_id, data.model, data.common_faults,data.device_name,
        data.last_maintenance_date, data.notes
    )


@router.post(
    "/device/{device_id}/fault",
    summary="添加故障记录",
    description="将新的故障记录添加到设备的常见故障 Top3 列表中",
    tags=["设备记忆"],
    responses={
        200: {
            "description": "添加成功",
            "example": {
                "status": "success",
                "message": "故障 E003 已添加到设备 BAT-001 的常见故障列表"
            }
        }
    }
)
async def add_device_fault(
    device_id: str,
    fault: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dify 工具：添加故障到设备常见故障 Top3
    """
    return await DeviceManager.add_fault_to_device(db, device_id, fault)


@router.post(
    "/cases/similar",
    summary="查找相似案例",
    description="根据故障码或症状描述查找历史解决方案，返回最匹配的案例列表",
    tags=["解决方案"],
    responses={
        200: {
            "description": "查询成功",
            "example": {
                "cases": [
                    {
                        "id": 1,
                        "error_code": "E003",
                        "symptoms": "温度显示 -40 度，插头腐蚀",
                        "solution": "清洗插头，涂抹接触保护剂，重新安装",
                        "solved_at": "2024-01-15T14:30:00"
                    }
                ],
                "total": 1
            }
        }
    }
)
async def find_similar_cases(
    query: SimilarCaseQuery,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dify 工具：查找相似案例

    根据故障码或症状描述查找历史解决方案
    """
    return await CaseMatcher.find_similar(db, query)


@router.post(
    "/solution/save",
    summary="保存解决方案",
    description="将诊断成功的解决方案保存到历史案例库，用于后续检索和参考",
    tags=["解决方案"],
    responses={
        200: {
            "description": "保存成功",
            "example": {
                "status": "success",
                "solution_id": 1,
                "message": "解决方案已保存"
            }
        }
    }
)
async def save_solution(
    record: SolutionRecord,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dify 工具：保存诊断解决方案

    将成功的诊断方案记录到历史解决方案表
    """
    return await DeviceManager.record_solution(db, record)


@router.get(
    "/error-code/{error_code}/history",
    summary="获取故障码历史",
    description="获取指定故障码的历史解决方案列表，按解决时间倒序排列",
    tags=["解决方案"],
    responses={
        200: {
            "description": "查询成功",
            "example": {
                "error_code": "E003",
                "solutions": [
                    {
                        "id": 1,
                        "symptoms": "温度显示 -40 度，插头腐蚀",
                        "solution": "清洗插头，涂抹接触保护剂",
                        "solved_at": "2024-01-15T14:30:00"
                    }
                ],
                "total": 1
            }
        }
    }
)
async def get_error_code_history(
    error_code: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dify 工具：获取某故障码的历史解决方案
    """
    from app.db.repository import SolutionRepository
    solutions = await SolutionRepository.get_by_error_code(db, error_code, limit)

    return {
        "error_code": error_code,
        "solutions": [
            {
                "id": s.id,
                "symptoms": s.symptoms,
                "solution": s.solution,
                "solved_at": s.solved_at.isoformat() if s.solved_at else None
            }
            for s in solutions
        ],
        "total": len(solutions)
    }
