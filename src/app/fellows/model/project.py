from datetime import date, datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sub: Mapped[int] = mapped_column(String, nullable=False)

    project_id: Mapped[int] = mapped_column(String, unique=True, nullable=False, default=str(uuid4()))
    project_info_id: Mapped[int] = mapped_column(ForeignKey("project_info.id"), unique=True, nullable=False)
    project_info: Mapped["ProjectInfo"] = relationship(back_populates="project", uselist=False)
    status: Mapped[str] = mapped_column(String, default="draft")  # 상태: draft, active, completed

    group_links: Mapped[List["ProjectGroupLink"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="subquery",
    )

    ai_estimate: Mapped[str] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @property
    def group_ids(self) -> List[str]:
        return [link.group_id for link in self.group_links]

    def add_group_id(self, group_id: str):
        if group_id not in self.group_ids:
            self.group_links.append(ProjectGroupLink(group_id=group_id))


class ProjectInfo(Base):
    __tablename__ = "project_info"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project: Mapped["Project"] = relationship(back_populates="project_info", uselist=False)

    # 필수 항목
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    project_summary: Mapped[str] = mapped_column(Text, nullable=False)
    platforms: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    readiness_level: Mapped[str] = mapped_column(String, nullable=False)

    # --- 디자인 요구사항 ---
    design_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- 기능 요구사항 ---
    feature_list: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    i18n_support: Mapped[bool] = mapped_column(Boolean, default=False)
    content_pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # --- 기술 및 환경 ---
    preferred_tech_stack: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    security_compliance: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # --- 일정 및 기타 ---
    start_date: Mapped[date | None] = mapped_column(Date, default=date.today, nullable=True)
    desired_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    maintenance_required: Mapped[bool] = mapped_column(Boolean, default=False)


class ProjectGroupLink(Base):
    __tablename__ = "project_group_link"

    project: Mapped["Project"] = relationship(back_populates="group_links")

    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), primary_key=True)
    group_id: Mapped[str] = mapped_column(String, primary_key=True)
