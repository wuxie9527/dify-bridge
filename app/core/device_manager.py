"""
设备管理器 - 设备相关业务逻辑（异步版本）
"""
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import DeviceRepository, SolutionRepository
from app.schemas.diagnosis import SolutionRecord

logger = logging.getLogger(__name__)


class DeviceManager:
    """设备管理器"""

    @staticmethod
    async def get_device(session: AsyncSession, device_id: str) -> Dict[str, Any]:
        """获取设备信息"""
        device = await DeviceRepository.get_by_device_id(session, device_id)

        if not device:
            return {"exists": False, "device_id": device_id}

        return {
            "exists": True,
            "data": {
                "device_id": device.device_id,
                "model": device.model,
                "common_faults": device.common_faults or [],
                "last_maintenance_date": device.last_maintenance_date.isoformat() if device.last_maintenance_date else None,
                "notes": device.notes
            }
        }

    @staticmethod
    async def create_or_update_device(
        session: AsyncSession,
        device_id: str,
        model: str = None,
        device_name: str = None,
        common_faults: list = None,
        last_maintenance_date: str = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """创建或更新设备"""
        data = {"device_id": device_id}
        if device_name:
            data["device_name"] = device_name
        if model:
            data["model"] = model
        if common_faults:
            data["common_faults"] = common_faults
        if last_maintenance_date:
            try:
                data["last_maintenance_date"] = datetime.fromisoformat(last_maintenance_date)
            except ValueError:
                pass
        if notes:
            data["notes"] = notes

        device = await DeviceRepository.create_or_update(session, data)

        return {
            "status": "success",
            "device_id": device.device_id,
            "created": device.created_at == device.updated_at
        }

    @staticmethod
    async def record_solution(session: AsyncSession, record: SolutionRecord) -> Dict[str, Any]:
        """记录解决方案"""
        solution_data = record.model_dump()
        if not solution_data.get("solved_at"):
            solution_data["solved_at"] = datetime.now()

        solution = await SolutionRepository.save(session, solution_data)

        return {
            "status": "success",
            "solution_id": solution.id,
            "message": "解决方案已保存"
        }

    @staticmethod
    async def get_device_history(
        session: AsyncSession,
        device_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """获取设备历史维修记录"""
        # 简化版：按 device_id 过滤需要从 solution 表关联，这里先返回空
        # 后续可以通过在 solution_history 表添加 device_id 字段来支持
        return {
            "history": [],
            "message": "当前版本不支持按设备查询历史，请按故障码查询"
        }

    @staticmethod
    async def add_fault_to_device(session: AsyncSession, device_id: str, fault: str) -> Dict[str, Any]:
        """添加故障记录到设备"""
        await DeviceRepository.add_fault(session, device_id, fault)
        return {
            "status": "success",
            "message": f"故障 {fault} 已添加到设备 {device_id} 的常见故障列表"
        }
