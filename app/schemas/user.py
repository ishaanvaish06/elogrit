from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data_region: str
    user_slug: str
    real_name: str
    avatar_url: str
    attended_contests_count: Optional[int] = None
    rating: Optional[float] = None
    global_ranking: Optional[int] = None
    updated_at: datetime


class UserContestHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data_region: str
    user_slug: str
    contest_title_slug: str
    attended: bool
    rating: float
    ranking: int
    trend_direction: str
    problems_solved: int
    total_problems: int
    finish_time_in_seconds: int
    updated_at: datetime


class UserRealTimeDataResponse(BaseModel):
    contest_title_slug: str
    data_region: str
    user_slug: str
    real_time_ranks: Optional[List[int]] = None
    real_time_ratings: Optional[List[float]] = None
