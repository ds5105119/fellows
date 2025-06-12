from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthorInlineDto(BaseModel):
    sub: str
    name: str
    bio: str | None = Field(None)
    picture: str | None = Field(None)


class CategoryInlineDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str | None = Field(None)


class TagInlineDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str


class BlogPostDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    title_image: str
    content: str
    summary: str | None = Field(None)
    is_published: bool = Field(False)
    published_at: datetime | None = Field(None)

    author: AuthorInlineDto
    category: CategoryInlineDto | None = Field(None)
    tags: list[TagInlineDto] = Field(default_factory=list)


class UpdateBlogPostDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(None)
    title_image: str | None = Field(None)
    content: str | None = Field(None)
    summary: str | None = Field(None)
    is_published: bool = Field(False)
    published_at: datetime | None = Field(None)

    category: CategoryInlineDto | None = Field(None)
    tags: list[TagInlineDto] = Field(default_factory=list)


class BlogPostListQueryDto(BaseModel):
    page: int = Field(default=0)
    size: int = Field(default=10, le=100)

    category: str | None = Field(None)
    tag: str | None = Field(None)
    keyword: str | None = Field(None)
    order_by: str | None = "published_at"
    descending: bool = True


class BlogPostPaginatedResponse(BaseModel):
    total: int
    items: list[BlogPostDto]
