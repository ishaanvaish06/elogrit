from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class RankingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contest_title_slug: str
    data_region: str
    user_slug: str
    rank: int
    score: int
    finish_time: datetime
    attended_contests_count: Optional[int] = None
    old_rating: Optional[float] = None
    expected_rating: Optional[float] = None
    delta_rating: Optional[float] = None
    new_rating: Optional[float] = None
    updated_at: datetime


class RankingListResponse(BaseModel):
    items: List[RankingResponse]
    total: int
    limit: int
    offset: int
