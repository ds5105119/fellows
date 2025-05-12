from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base


class FileRecord(Base):
    __tablename__ = "file_records"

    key: Mapped[str] = mapped_column(String, primary_key=True, unique=True)
    sub: Mapped[int] = mapped_column(String, nullable=False)
    algorithm: Mapped[str] = mapped_column(String, nullable=False, default="AES256")
    sse_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
