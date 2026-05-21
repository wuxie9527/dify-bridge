"""
数据访问层 - Repository 模式（异步版本）
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DeviceMemory, SolutionHistory, DiagnosisMemory


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
    async def create_or_update(session: AsyncSession, data: Dict[str, Any]) -> tuple[DeviceMemory, bool]:
        """创建或更新设备信息

        返回：(设备对象，是否新建)
        """
        device_id = data.get("device_id")
        existing = await DeviceRepository.get_by_device_id(session, device_id)

        if existing:
            # 更新
            for key, value in data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.updated_at = datetime.now()
            return existing, False
        else:
            # 创建
            device = DeviceMemory(**data)
            session.add(device)
            await session.flush()
            return device, True

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


class MemoryRepository:
    """长期记忆仓储"""

    @staticmethod
    async def create(session: AsyncSession, data: Dict[str, Any]) -> DiagnosisMemory:
        """创建记忆"""
        memory = DiagnosisMemory(**data)
        session.add(memory)
        await session.flush()
        await session.refresh(memory)
        return memory

    @staticmethod
    async def search(
        session: AsyncSession,
        query: str,
        device_id: Optional[str] = None,
        device_name: Optional[str] = None,
        error_code: Optional[str] = None,
        top_k: int = 5
    ) -> List[DiagnosisMemory]:
        """关键词检索记忆"""
        conditions = []

        # 关键词匹配（symptoms 字段）
        if query:
            conditions.append(
                DiagnosisMemory.symptoms.like(f"%{query}%")
            )

        # 设备编号过滤
        if device_id:
            conditions.append(
                DiagnosisMemory.device_id == device_id
            )

        # 设备名称过滤
        if device_name:
            conditions.append(
                DiagnosisMemory.device_name.like(f"%{device_name}%")
            )

        # 故障码过滤
        if error_code:
            conditions.append(
                DiagnosisMemory.error_code == error_code
            )

        # 构建查询
        stmt = select(DiagnosisMemory).where(*conditions) if conditions else select(DiagnosisMemory)

        # 排序：命中次数倒序 + 时间倒序
        stmt = stmt.order_by(
            desc(DiagnosisMemory.hit_count),
            desc(DiagnosisMemory.created_at)
        )

        # 限制数量
        stmt = stmt.limit(top_k)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, memory_id: int) -> Optional[DiagnosisMemory]:
        """根据 ID 获取记忆"""
        result = await session.execute(
            select(DiagnosisMemory).where(DiagnosisMemory.id == memory_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(session: AsyncSession, memory_id: int) -> bool:
        """删除记忆"""
        from sqlalchemy import delete
        stmt = delete(DiagnosisMemory).where(DiagnosisMemory.id == memory_id)
        result = await session.execute(stmt)
        return result.rowcount > 0

    @staticmethod
    async def increment_hit_count(session: AsyncSession, memory_id: int):
        """增加命中次数"""
        from sqlalchemy import update
        stmt = (
            update(DiagnosisMemory)
            .where(DiagnosisMemory.id == memory_id)
            .values(hit_count=DiagnosisMemory.hit_count + 1)
        )
        await session.execute(stmt)
