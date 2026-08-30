from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ContestBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title_slug: str
    start_time: datetime
    duration_seconds: int
    title_us: str
    title_cn: str
    unrated_us: bool = False
    unrated_cn: bool = False
    ranking_updated_us: bool = False
    ranking_updated_cn: bool = False
    register_user_num_us: int = 0
    register_user_num_cn: int = 0
    user_num_us: Optional[int] = None
    user_num_cn: Optional[int] = None
    discuss_url_us: Optional[str] = None
    discuss_url_cn: Optional[str] = None


class ContestResponse(ContestBase):
    updated_at: datetime
    contest_type: Optional[str] = None
    end_time: Optional[datetime] = None


class ContestListResponse(BaseModel):
    items: List[ContestResponse]
    total: int
