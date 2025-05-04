import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base


class Diagnostics(Base):
    __tablename__ = "diagnostics"
    __table_args__ = (PrimaryKeyConstraint("id", name="diagnostics_pkey"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    platform: Mapped[Optional[str]] = mapped_column(Text)
    architecture: Mapped[Optional[str]] = mapped_column(Text)
    plugin: Mapped[Optional[str]] = mapped_column(Text)
    cli_version: Mapped[Optional[str]] = mapped_column(Text)
    logs: Mapped[Optional[str]] = mapped_column(Text)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text)


class Durations(Base):
    __tablename__ = "durations"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="durations_pkey"),
        Index("idx_time_duration_user", "user_id", "time"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text)
    time: Mapped[datetime.datetime] = mapped_column(DateTime)
    duration: Mapped[int] = mapped_column(BigInteger)
    timeout: Mapped[int] = mapped_column(BigInteger, server_default=text("'600000000000'::bigint"))
    project: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[Optional[str]] = mapped_column(Text)
    editor: Mapped[Optional[str]] = mapped_column(Text)
    operating_system: Mapped[Optional[str]] = mapped_column(Text)
    machine: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(Text)
    branch: Mapped[Optional[str]] = mapped_column(Text)
    entity: Mapped[Optional[str]] = mapped_column(Text)
    num_heartbeats: Mapped[Optional[int]] = mapped_column(BigInteger)
    group_hash: Mapped[Optional[str]] = mapped_column(String(17))


class KeyStringValues(Base):
    __tablename__ = "key_string_values"
    __table_args__ = (PrimaryKeyConstraint("key", name="key_string_values_pkey"),)

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(Text)


class Users(Base):
    __tablename__ = "users"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="users_pkey"),
        UniqueConstraint("api_key", name="uni_users_api_key"),
        Index("idx_user_email", "email"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    api_key: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(Text)
    password: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    last_logged_in_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    share_data_max_days: Mapped[Optional[int]] = mapped_column(BigInteger)
    share_editors: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    share_languages: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    share_projects: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    share_oss: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    share_machines: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    share_labels: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    share_activity_chart: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    is_admin: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    has_data: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    wakatime_api_key: Mapped[Optional[str]] = mapped_column(Text)
    wakatime_api_url: Mapped[Optional[str]] = mapped_column(Text)
    reset_token: Mapped[Optional[str]] = mapped_column(Text)
    reports_weekly: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    public_leaderboard: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text("false"))
    subscribed_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    subscription_renewal: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(Text)
    invited_by: Mapped[Optional[str]] = mapped_column(Text)
    exclude_unknown_projects: Mapped[Optional[bool]] = mapped_column(Boolean)
    heartbeats_timeout_sec: Mapped[Optional[int]] = mapped_column(BigInteger, server_default=text("600"))

    aliases: Mapped[List["Aliases"]] = relationship("Aliases", back_populates="user")
    heartbeats: Mapped[List["Heartbeats"]] = relationship("Heartbeats", back_populates="user")
    language_mappings: Mapped[List["LanguageMappings"]] = relationship("LanguageMappings", back_populates="user")
    leaderboard_items: Mapped[List["LeaderboardItems"]] = relationship("LeaderboardItems", back_populates="user")
    project_labels: Mapped[List["ProjectLabels"]] = relationship("ProjectLabels", back_populates="user")
    summaries: Mapped[List["Summaries"]] = relationship("Summaries", back_populates="user")


class Aliases(Base):
    __tablename__ = "aliases"
    __table_args__ = (
        ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE", name="fk_aliases_user"),
        PrimaryKeyConstraint("id", name="aliases_pkey"),
        Index("idx_alias_type_key", "type", "key"),
        Index("idx_alias_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[int] = mapped_column(SmallInteger)
    user_id: Mapped[str] = mapped_column(Text)
    key: Mapped[str] = mapped_column(Text)
    value: Mapped[str] = mapped_column(Text)

    user: Mapped["Users"] = relationship("Users", back_populates="aliases")


class Heartbeats(Base):
    __tablename__ = "heartbeats"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE", name="fk_heartbeats_user"
        ),
        PrimaryKeyConstraint("id", name="heartbeats_pkey"),
        Index("idx_branch", "branch"),
        Index("idx_editor", "editor"),
        Index("idx_heartbeats_hash", "hash", unique=True),
        Index("idx_language", "language"),
        Index("idx_machine", "machine"),
        Index("idx_operating_system", "operating_system"),
        Index("idx_project", "project"),
        Index("idx_time", "time"),
        Index("idx_time_user", "user_id", "time"),
        Index("idx_user_project", "user_id", "project"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text)
    entity: Mapped[str] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(String(255))
    project: Mapped[Optional[str]] = mapped_column(Text)
    branch: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[Optional[str]] = mapped_column(Text)
    is_write: Mapped[Optional[bool]] = mapped_column(Boolean)
    editor: Mapped[Optional[str]] = mapped_column(Text)
    operating_system: Mapped[Optional[str]] = mapped_column(Text)
    machine: Mapped[Optional[str]] = mapped_column(Text)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    time: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))
    hash: Mapped[Optional[str]] = mapped_column(String(17))
    origin: Mapped[Optional[str]] = mapped_column(String(255))
    origin_id: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))
    lines: Mapped[Optional[int]] = mapped_column(BigInteger)
    line_no: Mapped[Optional[int]] = mapped_column(BigInteger)
    cursor_pos: Mapped[Optional[int]] = mapped_column(BigInteger)
    line_deletions: Mapped[Optional[int]] = mapped_column(BigInteger)
    line_additions: Mapped[Optional[int]] = mapped_column(BigInteger)
    project_root_count: Mapped[Optional[int]] = mapped_column(BigInteger)

    user: Mapped["Users"] = relationship("Users", back_populates="heartbeats")


class LanguageMappings(Base):
    __tablename__ = "language_mappings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE", name="fk_language_mappings_user"
        ),
        PrimaryKeyConstraint("id", name="language_mappings_pkey"),
        Index("idx_language_mapping_composite", "user_id", "extension", unique=True),
        Index("idx_language_mapping_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text)
    extension: Mapped[Optional[str]] = mapped_column(String(16))
    language: Mapped[Optional[str]] = mapped_column(String(64))

    user: Mapped["Users"] = relationship("Users", back_populates="language_mappings")


class LeaderboardItems(Base):
    __tablename__ = "leaderboard_items"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE", name="fk_leaderboard_items_user"
        ),
        PrimaryKeyConstraint("id", name="leaderboard_items_pkey"),
        Index("idx_leaderboard_combined", "interval", "by"),
        Index("idx_leaderboard_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text)
    interval: Mapped[str] = mapped_column(String(32))
    total: Mapped[int] = mapped_column(BigInteger)
    by: Mapped[Optional[int]] = mapped_column(SmallInteger)
    key: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    user: Mapped["Users"] = relationship("Users", back_populates="leaderboard_items")


class ProjectLabels(Base):
    __tablename__ = "project_labels"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE", name="fk_project_labels_user"
        ),
        PrimaryKeyConstraint("id", name="project_labels_pkey"),
        Index("idx_project_label_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text)
    project_key: Mapped[Optional[str]] = mapped_column(Text)
    label: Mapped[Optional[str]] = mapped_column(String(64))

    user: Mapped["Users"] = relationship("Users", back_populates="project_labels")


class Summaries(Base):
    __tablename__ = "summaries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE", name="fk_summaries_user"
        ),
        PrimaryKeyConstraint("id", name="summaries_pkey"),
        Index("idx_time_summary_user", "user_id", "from_time", "to_time"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[str] = mapped_column(Text)
    from_time: Mapped[datetime.datetime] = mapped_column(DateTime)
    to_time: Mapped[datetime.datetime] = mapped_column(DateTime)
    num_heartbeats: Mapped[Optional[int]] = mapped_column(BigInteger)

    user: Mapped["Users"] = relationship("Users", back_populates="summaries")
    summary_items: Mapped[List["SummaryItems"]] = relationship("SummaryItems", back_populates="summary")


class SummaryItems(Base):
    __tablename__ = "summary_items"
    __table_args__ = (
        ForeignKeyConstraint(
            ["summary_id"], ["summaries.id"], ondelete="CASCADE", onupdate="CASCADE", name="fk_summaries_projects"
        ),
        PrimaryKeyConstraint("id", name="summary_items_pkey"),
        Index("idx_type", "type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    summary_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    type: Mapped[Optional[int]] = mapped_column(SmallInteger)
    key: Mapped[Optional[str]] = mapped_column(String(255))
    total: Mapped[Optional[int]] = mapped_column(BigInteger)

    summary: Mapped[Optional["Summaries"]] = relationship("Summaries", back_populates="summary_items")
