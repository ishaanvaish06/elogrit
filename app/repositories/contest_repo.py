from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contest import Contest


class ContestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_slug(self, title_slug: str) -> Optional[Contest]:
        stmt = select(Contest).where(Contest.title_slug == title_slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_contests(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Contest], int]:
        now = datetime.now(timezone.utc)
        stmt = select(Contest)

        if status == "upcoming":
            stmt = stmt.where(Contest.start_time > now).order_by(asc(Contest.start_time))
        elif status == "past":
            stmt = stmt.where(Contest.start_time <= now).order_by(desc(Contest.start_time))
        else:
            stmt = stmt.order_by(desc(Contest.start_time))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        paged_stmt = stmt.limit(limit).offset(offset)
        items = (await self.session.execute(paged_stmt)).scalars().all()

        return list(items), total

    async def upsert(self, contest: Contest) -> Contest:
        existing = await self.get_by_slug(contest.title_slug)
        if existing:
            existing.start_time = contest.start_time
            existing.duration_seconds = contest.duration_seconds
            existing.title_us = contest.title_us
            existing.title_cn = contest.title_cn
            existing.unrated_us = contest.unrated_us
            existing.unrated_cn = contest.unrated_cn
            existing.ranking_updated_us = contest.ranking_updated_us
            existing.ranking_updated_cn = contest.ranking_updated_cn
            existing.register_user_num_us = contest.register_user_num_us
            existing.register_user_num_cn = contest.register_user_num_cn
            if contest.user_num_us is not None:
                existing.user_num_us = contest.user_num_us
            if contest.user_num_cn is not None:
                existing.user_num_cn = contest.user_num_cn
            if contest.discuss_url_us is not None:
                existing.discuss_url_us = contest.discuss_url_us
            if contest.discuss_url_cn is not None:
                existing.discuss_url_cn = contest.discuss_url_cn
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            self.session.add(contest)
            await self.session.commit()
            await self.session.refresh(contest)
            return contest

    async def upsert_many(self, contests: List[Contest]) -> int:
        count = 0
        for c in contests:
            await self.upsert(c)
            count += 1
        return count
