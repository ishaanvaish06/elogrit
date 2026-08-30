from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utc_now


class User(Base):
    __tablename__ = "users"

    data_region: Mapped[str] = mapped_column(String(16), primary_key=True)
    user_slug: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    real_name: Mapped[str] = mapped_column(String(256), default="")
    avatar_url: Mapped[str] = mapped_column(String(512), default="")
    attended_contests_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    global_ranking: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        Index("ix_users_slug_region", "user_slug", "data_region"),
    )


class UserContestHistory(Base):
    __tablename__ = "user_contest_histories"

    data_region: Mapped[str] = mapped_column(String(16), primary_key=True)
    user_slug: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    contest_title_slug: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    attended: Mapped[bool] = mapped_column(nullable=False, default=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    trend_direction: Mapped[str] = mapped_column(String(32), default="")
    problems_solved: Mapped[int] = mapped_column(Integer, default=0)
    total_problems: Mapped[int] = mapped_column(Integer, default=4)
    finish_time_in_seconds: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
