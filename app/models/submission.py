from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utc_now


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    question_id: Mapped[int] = mapped_column(Integer, index=True)
    data_region: Mapped[str] = mapped_column(String(16))
    user_slug: Mapped[str] = mapped_column(String(128), index=True)
    timepoint: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    lang: Mapped[str] = mapped_column(String(64), default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        Index("ix_submissions_user_question", "user_slug", "data_region", "question_id"),
    )
