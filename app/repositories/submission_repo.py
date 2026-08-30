from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission


class SubmissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user(self, data_region: str, user_slug: str) -> List[Submission]:
        stmt = (
            select(Submission)
            .where(
                Submission.data_region == data_region.upper(),
                Submission.user_slug == user_slug.lower(),
            )
            .order_by(Submission.timepoint.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_sync_submissions(self, submissions: List[Submission]) -> int:
        if not submissions:
            return 0
        # Upsert submissions
        for s in submissions:
            existing = await self.session.get(Submission, s.id)
            if existing:
                existing.question_id = s.question_id
                existing.data_region = s.data_region
                existing.user_slug = s.user_slug
                existing.timepoint = s.timepoint
                existing.fail_count = s.fail_count
                existing.lang = s.lang
                existing.updated_at = datetime.now(timezone.utc)
            else:
                self.session.add(s)
        await self.session.commit()
        return len(submissions)
