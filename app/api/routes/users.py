from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.ranking_repo import RankingRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserContestHistoryResponse, UserRealTimeDataResponse, UserResponse
from app.services.sourcing.user_sourcing import UserSourcing

router = APIRouter(tags=["Users"])


@router.get("/users/{data_region}/{user_slug}", response_model=UserResponse)
async def get_user_profile(
    data_region: str,
    user_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve user public profile and contest ranking stats."""
    region = data_region.upper()
    if region not in ("US", "CN"):
        raise HTTPException(status_code=400, detail="Invalid dataRegion. Must be US or CN.")

    repo = UserRepository(db)
    user = await repo.get_user(region, user_slug)
    if not user:
        # Attempt live lookup
        user = await UserSourcing.fetch_user(region, user_slug)
        if user:
            user = await repo.upsert_user(user)

    if not user:
        raise HTTPException(status_code=404, detail=f"User {region}/{user_slug} not found")

    return UserResponse.model_validate(user)


@router.get("/users/{data_region}/{user_slug}/history", response_model=List[UserContestHistoryResponse])
async def get_user_contest_history(
    data_region: str,
    user_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve historical contest performance for a user."""
    region = data_region.upper()
    if region not in ("US", "CN"):
        raise HTTPException(status_code=400, detail="Invalid dataRegion. Must be US or CN.")

    repo = UserRepository(db)
    histories = await repo.get_user_history(region, user_slug)
    if not histories:
        # Attempt live fetch
        histories = await UserSourcing.fetch_user_contest_history(region, user_slug)
        if histories:
            await repo.upsert_user_history(histories)

    return [UserContestHistoryResponse.model_validate(h) for h in histories]


@router.get("/contests/{title_slug}/users/{data_region}/{user_slug}/realtime", response_model=UserRealTimeDataResponse)
async def get_user_realtime_contest_data(
    title_slug: str,
    data_region: str,
    user_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve real-time rank and predicted rating progression for a user in a specific contest."""
    region = data_region.upper()
    if region not in ("US", "CN"):
        raise HTTPException(status_code=400, detail="Invalid dataRegion. Must be US or CN.")

    repo = RankingRepository(db)
    ranking = await repo.get_ranking(title_slug, region, user_slug)
    if not ranking:
        raise HTTPException(
            status_code=404,
            detail=f"Ranking entry not found for user {region}/{user_slug} in contest {title_slug}",
        )

    return UserRealTimeDataResponse(
        contest_title_slug=title_slug,
        data_region=region,
        user_slug=user_slug.lower(),
        real_time_ranks=ranking.real_time_ranks,
        real_time_ratings=ranking.real_time_ratings,
    )
