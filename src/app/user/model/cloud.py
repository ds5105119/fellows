from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base

if TYPE_CHECKING:
    from src.app.fellows.model.project import ProjectInfoFileRecordLink


class FileRecord(Base):
    __tablename__ = "file_records"

    key: Mapped[str] = mapped_column(String, primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String)
    sub: Mapped[int] = mapped_column(String, nullable=False)
    algorithm: Mapped[str] = mapped_column(String, nullable=False, default="AES256")
    sse_key: Mapped[str] = mapped_column(String, nullable=False)
    md5: Mapped[str] = mapped_column(String, nullable=False)

    project_info: Mapped[list["ProjectInfoFileRecordLink"]] = relationship(
        back_populates="file_record",
        cascade="all, delete-orphan",
    )
