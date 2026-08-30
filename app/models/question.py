from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utc_now


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_title_slug: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("contests.title_slug", ondelete="CASCADE"),
        index=True,
    )
    id_us: Mapped[int] = mapped_column(Integer)
    id_cn: Mapped[int] = mapped_column(Integer)
    title_slug: Mapped[str] = mapped_column(String(256), index=True)
    title_us: Mapped[str] = mapped_column(String(256))
    title_cn: Mapped[str] = mapped_column(String(256))
    difficulty: Mapped[int] = mapped_column(Integer)
    credit: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        Index("ix_questions_contest_id", "contest_title_slug", "id"),
    )
