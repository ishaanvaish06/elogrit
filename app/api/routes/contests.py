from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.contest_repo import ContestRepository
from app.repositories.question_count_repo import QuestionRealTimeCountRepository
from app.repositories.question_repo import QuestionRepository
from app.repositories.ranking_repo import RankingRepository
from app.schemas.contest import ContestListResponse, ContestResponse
from app.schemas.question import QuestionRealTimeCountResponse, QuestionResponse
from app.schemas.ranking import RankingListResponse, RankingResponse
from app.services.contest_service import ContestService

router = APIRouter(prefix="/contests", tags=["Contests"])


@router.get("", response_model=ContestListResponse)
async def list_contests(
    status: Optional[str] = Query(None, description="Filter by status: upcoming, past, or all"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List LeetCode contests with optional status filter and pagination."""
    if status and status not in ("upcoming", "past", "all"):
        raise HTTPException(status_code=400, detail="Invalid status filter. Choose upcoming, past, or all.")

    repo = ContestRepository(db)
    items, total = await repo.list_contests(status=status, limit=limit, offset=offset)
    return ContestListResponse(items=[ContestResponse.model_validate(c) for c in items], total=total)


@router.get("/{title_slug}", response_model=ContestResponse)
async def get_contest(
    title_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a specific contest by title slug."""
    repo = ContestRepository(db)
    contest = await repo.get_by_slug(title_slug)
    if not contest:
        raise HTTPException(status_code=404, detail=f"Contest {title_slug} not found")
    return ContestResponse.model_validate(contest)


@router.get("/{title_slug}/questions", response_model=List[QuestionResponse])
async def get_contest_questions(
    title_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """List all problems/questions for a specific contest."""
    repo = QuestionRepository(db)
    questions = await repo.get_by_contest(title_slug)
    return [QuestionResponse.model_validate(q) for q in questions]


@router.get("/{title_slug}/rankings", response_model=RankingListResponse)
async def get_contest_rankings(
    title_slug: str,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated contest rankings with Elo predicted ratings and deltas."""
    repo = RankingRepository(db)
    rankings, total = await repo.list_by_contest(title_slug, limit=limit, offset=offset)
    return RankingListResponse(
        items=[RankingResponse.model_validate(r) for r in rankings],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{title_slug}/question-counts", response_model=List[QuestionRealTimeCountResponse])
async def get_question_realtime_counts(
    title_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get minute-by-minute question solve milestones for the contest duration."""
    repo = QuestionRealTimeCountRepository(db)
    counts = await repo.get_by_contest(title_slug)
    return [QuestionRealTimeCountResponse.model_validate(c) for c in counts]


@router.post("/{title_slug}/sync")
async def sync_contest(
    title_slug: str,
    background_tasks: BackgroundTasks,
):
    """Trigger background metadata sync for a contest."""
    background_tasks.add_task(ContestService.sync_contest_metadata, title_slug)
    return {"message": f"Contest {title_slug} sync triggered in background"}


@router.post("/{title_slug}/predict")
async def predict_contest(
    title_slug: str,
    background_tasks: BackgroundTasks,
):
    """Trigger full data ingestion, user rating sync, and FFT Elo rating prediction."""
    background_tasks.add_task(ContestService.run_contest_prediction, title_slug)
    return {"message": f"Contest {title_slug} rating prediction pipeline triggered in background"}
