"""
数据访问层 - Repository 模式（异步版本）
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DeviceMemory, SolutionHistory


class DeviceRepository:
    """设备数据访问"""

    @staticmethod
    async def get_by_device_id(session: AsyncSession, device_id: str) -> Optional[DeviceMemory]:
        """根据设备 ID 获取设备信息"""
        result = await session.execute(
            select(DeviceMemory).where(DeviceMemory.device_id == device_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_or_update(session: AsyncSession, data: Dict[str, Any]) -> DeviceMemory:
        """创建或更新设备信息"""
        device_id = data.get("device_id")
        existing = await DeviceRepository.get_by_device_id(session, device_id)

        if existing:
            # 更新
            for key, value in data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.updated_at = datetime.now()
            return existing
        else:
            # 创建
            device = DeviceMemory(**data)
            session.add(device)
            await session.flush()
            return device

    @staticmethod
    async def add_fault(session: AsyncSession, device_id: str, fault: str):
        """添加故障记录到 common_faults Top3"""
        device = await DeviceRepository.get_by_device_id(session, device_id)
        if device:
            common_faults = device.common_faults or []
            if fault not in common_faults:
                common_faults.append(fault)
            device.common_faults = common_faults[-3:]  # 只保留 Top3

    @staticmethod
    async def update_maintenance_date(session: AsyncSession, device_id: str, date: datetime):
        """更新保养日期"""
        device = await DeviceRepository.get_by_device_id(session, device_id)
        if device:
            device.last_maintenance_date = date
            device.updated_at = datetime.now()


class SolutionRepository:
    """解决方案数据访问"""

    @staticmethod
    async def save(session: AsyncSession, data: Dict[str, Any]) -> SolutionHistory:
        """保存解决方案"""
        solution = SolutionHistory(**data)
        session.add(solution)
        await session.flush()
        return solution

    @staticmethod
    async def find_similar(
        session: AsyncSession,
        error_code: Optional[str] = None,
        symptoms: Optional[str] = None,
        limit: int = 5
    ) -> List[SolutionHistory]:
        """查找相似案例"""
        conditions = []

        if error_code:
            conditions.append(SolutionHistory.error_code == error_code)

        query = select(SolutionHistory)
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(SolutionHistory.solved_at)).limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_error_code(session: AsyncSession, error_code: str, limit: int = 10) -> List[SolutionHistory]:
        """获取某故障码的历史解决方案"""
        query = (
            select(SolutionHistory)
            .where(SolutionHistory.error_code == error_code)
            .order_by(desc(SolutionHistory.solved_at))
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())
