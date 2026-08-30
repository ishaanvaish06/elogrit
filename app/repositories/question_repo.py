from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question


class QuestionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_contest(self, contest_title_slug: str) -> List[Question]:
        stmt = (
            select(Question)
            .where(Question.contest_title_slug == contest_title_slug)
            .order_by(Question.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_many(self, questions: List[Question]) -> int:
        count = 0
        for q in questions:
            stmt = select(Question).where(Question.id == q.id)
            existing = (await self.session.execute(stmt)).scalar_one_or_none()
            if existing:
                existing.contest_title_slug = q.contest_title_slug
                existing.id_us = q.id_us
                existing.id_cn = q.id_cn
                existing.title_slug = q.title_slug
                existing.title_us = q.title_us
                existing.title_cn = q.title_cn
                existing.difficulty = q.difficulty
                existing.credit = q.credit
                existing.updated_at = datetime.now(timezone.utc)
            else:
                self.session.add(q)
            count += 1
        await self.session.commit()
        return count
