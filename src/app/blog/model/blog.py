from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base


class Author(Base):
    __tablename__ = "author"

    sub: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(String(200), nullable=True)
    picture: Mapped[str | None] = mapped_column(String(200), nullable=True)

    posts: Mapped[list["BlogPost"]] = relationship(back_populates="author")


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    posts: Mapped[list["BlogPost"]] = relationship(back_populates="category")


class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    tag_posts: Mapped[list["PostTag"]] = relationship(back_populates="tag", cascade="all, delete-orphan")
    posts: Mapped[list["BlogPost"]] = relationship(secondary="post_tag", back_populates="tags", viewonly=True)


class PostTag(Base):
    __tablename__ = "post_tag"

    post_id: Mapped[int] = mapped_column(ForeignKey("blog_post.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tag.id"), primary_key=True)

    post: Mapped["BlogPost"] = relationship(back_populates="post_tags")
    tag: Mapped["Tag"] = relationship(back_populates="tag_posts")


class BlogPost(Base):
    __tablename__ = "blog_post"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_image: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    author_sub: Mapped[int] = mapped_column(ForeignKey("author.sub"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=True)

    author: Mapped["Author"] = relationship(back_populates="posts")
    category: Mapped["Category"] = relationship(back_populates="posts")

    post_tags: Mapped[list["PostTag"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship(
        secondary="post_tag",
        back_populates="posts",
        viewonly=True,
        cascade="all, delete-orphan",
    )
