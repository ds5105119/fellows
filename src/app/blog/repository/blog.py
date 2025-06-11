from sqlalchemy.ext.asyncio import AsyncSession

from src.app.blog.model.blog import Author, BlogPost, Category, PostTag, Tag
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class AuthorCreateRepository(ABaseCreateRepository[Author]):
    pass


class AuthorReadRepository(ABaseReadRepository[Author]):
    async def get_by_sub(self, session: AsyncSession, sub: str):
        result = await self.get(session, filters=[self.model.sub == sub])
        return result.scalars().one_or_none()


class AuthorUpdateRepository(ABaseUpdateRepository[Author]):
    pass


class AuthorDeleteRepository(ABaseDeleteRepository[Author]):
    pass


class BlogPostCreateRepository(ABaseCreateRepository[BlogPost]):
    pass


class BlogPostReadRepository(ABaseReadRepository[BlogPost]):
    pass


class BlogPostUpdateRepository(ABaseUpdateRepository[BlogPost]):
    pass


class BlogPostDeleteRepository(ABaseDeleteRepository[BlogPost]):
    pass


class CategoryCreateRepository(ABaseCreateRepository[Category]):
    pass


class CategoryReadRepository(ABaseReadRepository[Category]):
    async def get_by_name(self, session: AsyncSession, name: str):
        result = await self.get(session, filters=[self.model.name == name])
        return result.scalars().one_or_none()


class CategoryUpdateRepository(ABaseUpdateRepository[Category]):
    pass


class CategoryDeleteRepository(ABaseDeleteRepository[Category]):
    pass


class PostTagCreateRepository(ABaseCreateRepository[PostTag]):
    pass


class PostTagReadRepository(ABaseReadRepository[PostTag]):
    pass


class PostTagUpdateRepository(ABaseUpdateRepository[PostTag]):
    pass


class PostTagDeleteRepository(ABaseDeleteRepository[PostTag]):
    pass


class TagCreateRepository(ABaseCreateRepository[Tag]):
    pass


class TagReadRepository(ABaseReadRepository[Tag]):
    async def get_by_name(self, session: AsyncSession, name: str):
        result = await self.get(session, filters=[self.model.name == name])
        return result.scalars().one_or_none()


class TagUpdateRepository(ABaseUpdateRepository[Tag]):
    pass


class TagDeleteRepository(ABaseDeleteRepository[Tag]):
    pass


class AuthorRepository(
    AuthorCreateRepository,
    AuthorReadRepository,
    AuthorUpdateRepository,
    AuthorDeleteRepository,
):
    pass


class BlogPostRepository(
    BlogPostCreateRepository,
    BlogPostReadRepository,
    BlogPostUpdateRepository,
    BlogPostDeleteRepository,
):
    pass


class CategoryRepository(
    CategoryCreateRepository,
    CategoryReadRepository,
    CategoryUpdateRepository,
    CategoryDeleteRepository,
):
    pass


class PostTagRepository(
    PostTagCreateRepository,
    PostTagReadRepository,
    PostTagUpdateRepository,
    PostTagDeleteRepository,
):
    pass


class TagRepository(
    TagCreateRepository,
    TagReadRepository,
    TagUpdateRepository,
    TagDeleteRepository,
):
    pass
