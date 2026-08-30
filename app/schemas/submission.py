from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    data_region: str
    user_slug: str
    timepoint: datetime
    fail_count: int
    lang: str
    updated_at: datetime
