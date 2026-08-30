from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utc_now


class Contest(Base):
    __tablename__ = "contests"

    title_slug: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    title_us: Mapped[str] = mapped_column(String(256))
    title_cn: Mapped[str] = mapped_column(String(256))
    unrated_us: Mapped[bool] = mapped_column(Boolean, default=False)
    unrated_cn: Mapped[bool] = mapped_column(Boolean, default=False)
    ranking_updated_us: Mapped[bool] = mapped_column(Boolean, default=False)
    ranking_updated_cn: Mapped[bool] = mapped_column(Boolean, default=False)
    register_user_num_us: Mapped[int] = mapped_column(Integer, default=0)
    register_user_num_cn: Mapped[int] = mapped_column(Integer, default=0)
    user_num_us: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_num_cn: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    discuss_url_us: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    discuss_url_cn: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    @property
    def contest_type(self) -> Optional[str]:
        if "biweekly-contest" in self.title_slug:
            return "Biweekly"
        elif "weekly-contest" in self.title_slug:
            return "Weekly"
        return None

    @property
    def end_time(self) -> datetime:
        from datetime import timedelta
        return self.start_time + timedelta(seconds=self.duration_seconds)
