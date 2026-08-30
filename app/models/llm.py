from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utc_now


class Llm(Base):
    __tablename__ = "llms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    logo_url: Mapped[str] = mapped_column(String(512), default="")
    company_name: Mapped[str] = mapped_column(String(128), default="")
    info: Mapped[str] = mapped_column(String(1024), default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class LlmContestRanking(Base):
    __tablename__ = "llm_contest_rankings"

    llm_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_slug: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, default=0.0)
    ac_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_tried_times: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
