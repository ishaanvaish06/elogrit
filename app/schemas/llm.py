from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class LlmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    logo_url: str
    company_name: str
    info: str
    updated_at: datetime


class LlmContestRankingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    llm_id: int
    contest_slug: str
    avg_score: float
    max_score: float
    ac_rate: float
    avg_tried_times: float
    updated_at: datetime
    llm: Optional[LlmResponse] = None
