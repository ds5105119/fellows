from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.user.model.cloud import FileRecord
from src.core.models.base import Base


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sub: Mapped[int] = mapped_column(String, nullable=False)

    project_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=lambda: str(uuid4()))

    project_info: Mapped["ProjectInfo"] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        single_parent=True,
        uselist=False,
        passive_deletes=True,
    )

    status: Mapped[str] = mapped_column(String, default="draft")
    ai_estimate: Mapped[str] = mapped_column(Text, nullable=True)
    emoji: Mapped[str] = mapped_column(String, nullable=True)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    deletable: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def group_ids(self) -> list[str]:
        return [link.group_id for link in self.groups]

    def add_group_id(self, group_id: str):
        if group_id not in self.group_ids:
            self.groups.append(ProjectGroups(group_id=group_id))


class ProjectInfo(Base):
    __tablename__ = "project_info"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    project_id = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), unique=True, nullable=False)
    project: Mapped["Project"] = relationship(back_populates="project_info", uselist=False)

    # 필수 항목
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    project_summary: Mapped[str] = mapped_column(Text, nullable=False)
    platforms: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    readiness_level: Mapped[str] = mapped_column(String, nullable=False)

    # --- 기능 요구사항 ---
    feature_list: Mapped[list[str]] = mapped_column(ARRAY(String), default=lambda: list())
    content_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_tech_stack: Mapped[list[str]] = mapped_column(ARRAY(String), default=lambda: list())

    # --- 디자인 ---
    design_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_design_url: Mapped[list[str]] = mapped_column(ARRAY(String), default=lambda: list())
    files: Mapped[list["ProjectInfoFileRecordLink"]] = relationship(
        back_populates="project_info",
        cascade="all, delete-orphan",
        lazy="subquery",
    )

    # --- 일정 및 기타 ---
    start_date: Mapped[date | None] = mapped_column(Date, default=date.today, nullable=True)
    desired_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    maintenance_required: Mapped[bool] = mapped_column(Boolean, default=False)


class ProjectInfoFileRecordLink(Base):
    __tablename__ = "project_file_record_links"

    project_info_id: Mapped[int] = mapped_column(ForeignKey("project_info.id", ondelete="CASCADE"), primary_key=True)
    project_info: Mapped["ProjectInfo"] = relationship(back_populates="files")

    file_record_key: Mapped[str] = mapped_column(ForeignKey("file_records.key", ondelete="CASCADE"), primary_key=True)
    file_record: Mapped["FileRecord"] = relationship(back_populates="project_info")
