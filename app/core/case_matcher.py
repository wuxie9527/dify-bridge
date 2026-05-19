"""
案例匹配器 - 历史案例检索和匹配（异步版本）
"""
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import SolutionRepository
from app.schemas.diagnosis import SimilarCaseQuery

logger = logging.getLogger(__name__)


class CaseMatcher:
    """案例匹配器"""

    @staticmethod
    async def find_similar(
        session: AsyncSession,
        query: SimilarCaseQuery
    ) -> Dict[str, Any]:
        """查找相似案例"""
        cases = await SolutionRepository.find_similar(
            session,
            error_code=query.error_code,
            symptoms=query.symptoms if query.symptoms else None,
            limit=query.limit
        )

        return {
            "cases": [
                {
                    "id": c.id,
                    "error_code": c.error_code,
                    "symptoms": c.symptoms,
                    "solution": c.solution,
                    "solved_at": c.solved_at.isoformat() if c.solved_at else None
                }
                for c in cases
            ],
            "total": len(cases)
        }
