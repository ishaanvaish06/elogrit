from datetime import datetime
from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question_count import QuestionRealTimeCount


class QuestionRealTimeCountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_contest(self, contest_title_slug: str) -> List[QuestionRealTimeCount]:
        stmt = (
            select(QuestionRealTimeCount)
            .where(QuestionRealTimeCount.contest_title_slug == contest_title_slug)
            .order_by(
                QuestionRealTimeCount.question_id.asc(),
                QuestionRealTimeCount.time_index.asc(),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_counts(self, counts: List[QuestionRealTimeCount]) -> int:
        if not counts:
            return 0
        slug = counts[0].contest_title_slug
        del_stmt = delete(QuestionRealTimeCount).where(
            QuestionRealTimeCount.contest_title_slug == slug
        )
        await self.session.execute(del_stmt)
        self.session.add_all(counts)
        await self.session.commit()
        return len(counts)
