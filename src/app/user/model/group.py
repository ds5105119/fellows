from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base


class Group(Base):
    __tablename__ = "groups"
    id: Mapped[str] = mapped_column(String, primary_key=True, unique=True)

    parent_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True,
    )
    parent: Mapped[Optional["Group"]] = relationship(
        back_populates="children",
        remote_side=[id],
    )
    children: Mapped[list["Group"]] = relationship(
        back_populates="parent",
    )

    memberships: Mapped[list["GroupMembershipPositionLink"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    positions: Mapped[list["GroupPosition"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list["GroupInvitation"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_sub: Mapped[str | None] = mapped_column(String, nullable=True)
    group_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    role_view_groups: Mapped[int] = mapped_column(Integer, nullable=True, default=3)
    role_edit_groups: Mapped[int] = mapped_column(Integer, nullable=True, default=1)
    role_create_sub_groups: Mapped[int] = mapped_column(Integer, nullable=True, default=2)
    role_invite_groups: Mapped[int] = mapped_column(Integer, nullable=True, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class GroupPosition(Base):
    __tablename__ = "group_positions"
    __table_args__ = (UniqueConstraint("group_id", "name", name="uq_group_position_group_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    group: Mapped["Group"] = relationship(back_populates="positions")

    memberships: Mapped[list["GroupMembershipPositionLink"]] = relationship(back_populates="position")

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class GroupMembershipPositionLink(Base):
    __tablename__ = "group_membership_links"

    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    group: Mapped["Group"] = relationship(back_populates="memberships")

    membership_sub: Mapped[int] = mapped_column(ForeignKey("memberships.sub", ondelete="CASCADE"), primary_key=True)
    membership: Mapped["GroupMembership"] = relationship(back_populates="groups")

    position_id: Mapped[int] = mapped_column(Integer, ForeignKey("group_positions.id"), nullable=True)
    position: Mapped["GroupPosition"] = relationship(back_populates="memberships")

    role: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class GroupMembership(Base):
    __tablename__ = "memberships"
    sub: Mapped[str] = mapped_column(String, primary_key=True)

    groups: Mapped[list["GroupMembershipPositionLink"]] = relationship(back_populates="membership")


class GroupSchedule(Base):
    __tablename__ = "group_schedules"
    __table_args__ = (
        UniqueConstraint("group_id", "membership_sub", name="uq_group_schedule_entry"),
        Index("idx_schedule_group_date", "group_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    group: Mapped["Group"] = relationship()

    membership_sub: Mapped[str] = mapped_column(ForeignKey("memberships.sub", ondelete="CASCADE"))
    membership: Mapped["GroupMembership"] = relationship()

    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    work_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    start_planned: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_planned: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hours_actual: Mapped[float] = mapped_column(nullable=False, default=0.0)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class GroupInvitation(Base):
    __tablename__ = "group_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    group_id: Mapped[str] = mapped_column(String, ForeignKey("groups.id", ondelete="CASCADE"))
    group: Mapped["Group"] = relationship(back_populates="invitations")

    inviter_sub: Mapped[str] = mapped_column(String, nullable=False)
    inviter_email: Mapped[str] = mapped_column(String, nullable=False)
    invitee_email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[int] = mapped_column(Integer, nullable=True)

    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
