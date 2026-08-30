from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utc_now


class Ranking(Base):
    __tablename__ = "rankings"

    contest_title_slug: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("contests.title_slug", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    data_region: Mapped[str] = mapped_column(String(16), primary_key=True)
    user_slug: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    rank: Mapped[int] = mapped_column(Integer, index=True)
    score: Mapped[int] = mapped_column(Integer)
    finish_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attended_contests_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    old_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delta_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    real_time_ranks: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    real_time_ratings: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    @property
    def new_rating(self) -> Optional[float]:
        if self.old_rating is not None and self.delta_rating is not None:
            return round(self.old_rating + self.delta_rating, 2)
        return None

    __table_args__ = (
        Index("ix_rankings_contest_rank", "contest_title_slug", "rank"),
    )
