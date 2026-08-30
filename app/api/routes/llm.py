from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.llm_repo import LlmRepository
from app.schemas.llm import LlmContestRankingResponse, LlmResponse

router = APIRouter(tags=["LLM Analytics"])


@router.get("/llm", response_model=List[LlmResponse])
async def list_llm_models(
    db: AsyncSession = Depends(get_db),
):
    """List all tracked AI models and their metadata."""
    repo = LlmRepository(db)
    models = await repo.get_all_llms()
    return [LlmResponse.model_validate(m) for m in models]


@router.get("/contests/{contest_slug}/llm", response_model=List[LlmContestRankingResponse])
async def get_contest_llm_rankings(
    contest_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve performance scores, acceptance rates, and stats for LLMs in a contest."""
    repo = LlmRepository(db)
    rankings = await repo.get_rankings_by_contest(contest_slug)
    results: List[LlmContestRankingResponse] = []
    for r in rankings:
        llm = await repo.get_llm(r.llm_id)
        res = LlmContestRankingResponse(
            llm_id=r.llm_id,
            contest_slug=r.contest_slug,
            avg_score=r.avg_score,
            max_score=r.max_score,
            ac_rate=r.ac_rate,
            avg_tried_times=r.avg_tried_times,
            updated_at=r.updated_at,
            llm=LlmResponse.model_validate(llm) if llm else None,
        )
        results.append(res)
    return results
