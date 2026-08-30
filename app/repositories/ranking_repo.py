from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc, asc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ranking import Ranking
from app.models.user import User


class RankingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_ranking(self, contest_title_slug: str, data_region: str, user_slug: str) -> Optional[Ranking]:
        stmt = select(Ranking).where(
            Ranking.contest_title_slug == contest_title_slug,
            Ranking.data_region == data_region.upper(),
            Ranking.user_slug == user_slug.lower(),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_contest(
        self,
        contest_title_slug: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Ranking], int]:
        base_stmt = select(Ranking).where(
            Ranking.contest_title_slug == contest_title_slug,
            Ranking.score > 0,
        )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        paged_stmt = base_stmt.order_by(asc(Ranking.rank)).limit(limit).offset(offset)
        items = (await self.session.execute(paged_stmt)).scalars().all()

        return list(items), total

    async def get_all_by_contest(self, contest_title_slug: str) -> List[Ranking]:
        stmt = (
            select(Ranking)
            .where(Ranking.contest_title_slug == contest_title_slug, Ranking.score > 0)
            .order_by(asc(Ranking.rank))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_ids_by_contest(
        self,
        contest_title_slug: str,
        positive_score_only: bool = True,
    ) -> List[Tuple[str, str]]:
        stmt = select(Ranking.data_region, Ranking.user_slug).where(
            Ranking.contest_title_slug == contest_title_slug
        )
        if positive_score_only:
            stmt = stmt.where(Ranking.score > 0)
        stmt = stmt.order_by(asc(Ranking.rank))
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def bulk_sync_by_contest(self, contest_title_slug: str, rankings: List[Ranking]) -> int:
        # Delete existing rankings for the contest
        del_stmt = delete(Ranking).where(Ranking.contest_title_slug == contest_title_slug)
        await self.session.execute(del_stmt)

        # Insert new rankings
        self.session.add_all(rankings)
        await self.session.commit()
        return len(rankings)

    async def fill_user_old_rating_info(
        self,
        contest_title_slug: str,
        default_contests_count: int = 0,
        default_rating: float = 1500.0,
    ) -> int:
        """Enriches rankings with users' previous rating and attended contest count."""
        rankings = await self.get_all_by_contest(contest_title_slug)
        count = 0
        for r in rankings:
            user_stmt = select(User).where(
                User.data_region == r.data_region,
                User.user_slug == r.user_slug,
            )
            user = (await self.session.execute(user_stmt)).scalar_one_or_none()
            if user:
                r.attended_contests_count = (
                    user.attended_contests_count
                    if user.attended_contests_count is not None
                    else default_contests_count
                )
                r.old_rating = (
                    user.rating
                    if user.rating is not None
                    else default_rating
                )
            else:
                if r.attended_contests_count is None:
                    r.attended_contests_count = default_contests_count
                if r.old_rating is None:
                    r.old_rating = default_rating
            count += 1

        await self.session.commit()
        return count
