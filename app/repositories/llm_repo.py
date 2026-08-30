from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm import Llm, LlmContestRanking


class LlmRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_llms(self) -> List[Llm]:
        stmt = select(Llm).order_by(Llm.id.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_llm(self, llm_id: int) -> Optional[Llm]:
        return await self.session.get(Llm, llm_id)

    async def upsert_llm(self, llm: Llm) -> Llm:
        existing = await self.get_llm(llm.id)
        if existing:
            existing.name = llm.name
            existing.logo_url = llm.logo_url
            existing.company_name = llm.company_name
            existing.info = llm.info
            existing.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            self.session.add(llm)
            await self.session.commit()
            await self.session.refresh(llm)
            return llm

    async def upsert_llms(self, llms: List[Llm]) -> int:
        count = 0
        for m in llms:
            await self.upsert_llm(m)
            count += 1
        return count

    async def get_rankings_by_contest(self, contest_slug: str) -> List[LlmContestRanking]:
        stmt = (
            select(LlmContestRanking)
            .where(LlmContestRanking.contest_slug == contest_slug)
            .order_by(LlmContestRanking.avg_score.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_contest_rankings(self, rankings: List[LlmContestRanking]) -> int:
        count = 0
        for r in rankings:
            stmt = select(LlmContestRanking).where(
                LlmContestRanking.llm_id == r.llm_id,
                LlmContestRanking.contest_slug == r.contest_slug,
            )
            existing = (await self.session.execute(stmt)).scalar_one_or_none()
            if existing:
                existing.avg_score = r.avg_score
                existing.max_score = r.max_score
                existing.ac_rate = r.ac_rate
                existing.avg_tried_times = r.avg_tried_times
                existing.updated_at = datetime.now(timezone.utc)
            else:
                self.session.add(r)
            count += 1
        await self.session.commit()
        return count
