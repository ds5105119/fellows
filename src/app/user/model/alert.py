from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base


class Alert(Base):
    __tablename__ = "user_alert"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sub: Mapped[int] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    link: Mapped[str] = mapped_column(String, nullable=False)
