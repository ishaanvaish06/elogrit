from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contest_title_slug: str
    id_us: int
    id_cn: int
    title_slug: str
    title_us: str
    title_cn: str
    difficulty: int
    credit: int
    updated_at: datetime


class QuestionRealTimeCountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contest_title_slug: str
    question_id: int
    time_index: int
    count: int
