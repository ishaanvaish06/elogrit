from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utc_now


class QuestionRealTimeCount(Base):
    __tablename__ = "question_real_time_counts"

    contest_title_slug: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time_index: Mapped[int] = mapped_column(Integer, primary_key=True)  # minute index (1..90)
    count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
