from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserContestHistory


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, data_region: str, user_slug: str) -> Optional[User]:
        stmt = select(User).where(
            User.data_region == data_region.upper(),
            User.user_slug == user_slug.lower(),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_recently_updated(self, data_region: str, user_slug: str, since: datetime) -> bool:
        user = await self.get_user(data_region, user_slug)
        if not user:
            return False
        return user.updated_at >= since

    async def upsert_user(self, user: User) -> User:
        existing = await self.get_user(user.data_region, user.user_slug)
        if existing:
            existing.real_name = user.real_name
            existing.avatar_url = user.avatar_url
            if user.attended_contests_count is not None:
                existing.attended_contests_count = user.attended_contests_count
            if user.rating is not None:
                existing.rating = user.rating
            if user.global_ranking is not None:
                existing.global_ranking = user.global_ranking
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user

    async def upsert_users(self, users: List[User]) -> int:
        count = 0
        for u in users:
            await self.upsert_user(u)
            count += 1
        return count

    async def get_user_history(self, data_region: str, user_slug: str) -> List[UserContestHistory]:
        stmt = (
            select(UserContestHistory)
            .where(
                UserContestHistory.data_region == data_region.upper(),
                UserContestHistory.user_slug == user_slug.lower(),
            )
            .order_by(UserContestHistory.contest_title_slug.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_user_history(self, histories: List[UserContestHistory]) -> int:
        count = 0
        for h in histories:
            stmt = select(UserContestHistory).where(
                UserContestHistory.data_region == h.data_region.upper(),
                UserContestHistory.user_slug == h.user_slug.lower(),
                UserContestHistory.contest_title_slug == h.contest_title_slug,
            )
            existing = (await self.session.execute(stmt)).scalar_one_or_none()
            if existing:
                existing.attended = h.attended
                existing.rating = h.rating
                existing.ranking = h.ranking
                existing.trend_direction = h.trend_direction
                existing.problems_solved = h.problems_solved
                existing.total_problems = h.total_problems
                existing.finish_time_in_seconds = h.finish_time_in_seconds
                existing.updated_at = datetime.now(timezone.utc)
            else:
                self.session.add(h)
            count += 1
        await self.session.commit()
        return count
