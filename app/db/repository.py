"""
数据访问层 - Repository 模式（异步版本）
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DiagnosisMemory


class MemoryRepository:
    """长期记忆仓储"""

    @staticmethod
    async def create_or_update(session: AsyncSession, data: Dict[str, Any]) -> tuple[DiagnosisMemory, bool]:
        """创建或更新记忆（根据 error_code 判断）

        返回：(记忆对象，是否新建)
        """
        error_code = data.get("error_code")

        # 如果有 error_code，先查找是否已存在
        if error_code:
            existing = await MemoryRepository.get_by_error_code(session, error_code)
            if existing:
                # 更新现有记录
                for key, value in data.items():
                    if value is not None and hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
                return existing, False

        # 新增记录
        memory = DiagnosisMemory(**data)
        session.add(memory)
        await session.flush()
        await session.refresh(memory)
        return memory, True

    @staticmethod
    async def get_by_error_code(session: AsyncSession, error_code: str) -> Optional[DiagnosisMemory]:
        """根据 error_code 获取记忆"""
        result = await session.execute(
            select(DiagnosisMemory).where(DiagnosisMemory.error_code == error_code)
        )
        return result.scalar_one_or_none()

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

        # 如果没有任何条件，返回空列表（避免返回全表数据）
        if not conditions:
            return []

        # 构建查询
        stmt = select(DiagnosisMemory).where(*conditions)

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
