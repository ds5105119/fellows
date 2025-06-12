from secrets import randbelow
from typing import Annotated

from fastapi import HTTPException, Path, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.app.blog.repository.blog import (
    AuthorRepository,
    BlogPostRepository,
    CategoryRepository,
    PostTagRepository,
    TagRepository,
)
from src.app.blog.schema.blog import *
from src.core.dependencies.auth import get_current_user, get_current_user_without_error
from src.core.dependencies.db import postgres_session


def generate_date_based_12_digit_id() -> str:
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = f"{randbelow(10000):04}"
    return date_part + random_part


class BlogService:
    def __init__(
        self,
        author_repo: AuthorRepository,
        blog_post_repo: BlogPostRepository,
        category_repo: CategoryRepository,
        post_tag_repo: PostTagRepository,
        tag_repo: TagRepository,
    ):
        self.author_repo = author_repo
        self.blog_post_repo = blog_post_repo
        self.category_repo = category_repo
        self.post_tag_repo = post_tag_repo
        self.tag_repo = tag_repo

    async def generate_unique_post_id(self, session, max_tries: int = 10) -> int:
        for _ in range(max_tries):
            new_id = generate_date_based_12_digit_id()
            existing = await self.blog_post_repo.get_by_id(session, new_id)
            if not existing.one_or_none():
                return new_id
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate unique blog post ID."
        )

    async def create_blog_post(
        self,
        data: UpsertBlogPostDto,
        session: postgres_session,
        user: get_current_user,
    ):
        if "/manager" not in user.groups:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        author = await self.author_repo.get_by_sub(session, user.sub)
        updated_author = {}
        if not author:
            await self.author_repo.create(session, sub=user.sub, name=user.name, bio=user.bio)
        if author.name != user.name:
            updated_author.name = user.name
        if author.bio != user.bio:
            updated_author.bio = user.bio
        if updated_author:
            await self.author_repo.update(
                session,
                [self.author_repo.model.sub == user.sub],
                **updated_author,
            )

        category = await self.category_repo.get_by_name(session, data.category.name)
        if not category:
            category = await self.category_repo.create(session, **data.category.model_dump())

        post_id = await self.generate_unique_post_id(session)

        try:
            post = await self.blog_post_repo.create(
                session,
                id=post_id,
                author_sub=user.sub,
                category_id=category.id,
                title=data.title,
                title_image=data.title_image,
                content=data.content,
                summary=data.summary,
                is_published=data.is_published,
                published_at=data.published_at,
            )
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Post creation failed.")

        tag_ids = []
        for tag_dto in data.tags:
            tag = await self.tag_repo.get_by_name(session, tag_dto.name)
            if not tag:
                tag = await self.tag_repo.create(session, **tag_dto.model_dump())
            tag_ids.append(tag.id)

        if tag_ids:
            post_tag_objects = [{"post_id": post.id, "tag_id": tag_id} for tag_id in tag_ids]
            await self.post_tag_repo.bulk_create(session, post_tag_objects)

        return await self.get_post_by_id(session, post.id)

    async def get_post_by_id(
        self,
        session: postgres_session,
        post_id: int = Path(),
    ):
        result = await self.blog_post_repo.get_instance(
            session,
            filters=[self.blog_post_repo.model.id == post_id],
            options=[
                selectinload(self.blog_post_repo.model.author),
                selectinload(self.blog_post_repo.model.category),
                selectinload(self.blog_post_repo.model.tags),
            ],
        )
        post = result.scalars().one_or_none()

        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return BlogPostDto.model_validate(post, from_attributes=True)

    async def get_posts(
        self,
        data: Annotated[BlogPostListQueryDto, Query()],
        session: postgres_session,
        user: get_current_user_without_error,
    ):
        filters = []

        if not user or (user and "/manager" not in user.groups):
            filters.append(self.blog_post_repo.model.is_published == True)
        if data.category:
            filters.append(self.category_repo.model.name == data.category)
        if data.tag:
            filters.append(self.tag_repo.model.name == data.tag)
        if data.keyword:
            filters.append(self.blog_post_repo.model.content.contains(data.keyword))
            filters.append(self.blog_post_repo.model.title.contains(data.keyword))

        order_column = getattr(self.blog_post_repo.model, data.order_by or "published_at")

        result = await self.blog_post_repo.get_page_with_total(
            session,
            page=data.page,
            size=data.size,
            filters=filters,
            orderby=[order_column.desc() if data.descending else order_column],
            join=[self.blog_post_repo.model.tags],
            options=[
                selectinload(self.blog_post_repo.model.tags),
                selectinload(self.blog_post_repo.model.author),
                selectinload(self.blog_post_repo.model.category),
            ],
        )

        return BlogPostPaginatedResponse.model_validate(result, from_attributes=True)

    async def update_post(
        self,
        user: get_current_user,
        data: UpsertBlogPostDto,
        session: postgres_session,
        post_id: int,
    ):
        # 포스트 불러오기
        post = await self.get_post_by_id(session, post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if post.author.sub != user.sub:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        update_data = data.model_dump(exclude_unset=True, exclude={"category", "tags"})

        # 2. 카테고리 처리
        if "category" in data.model_fields_set:
            if data.category:
                category = await self.category_repo.get_by_name(session, data.category.name)
                if not category:
                    category = await self.category_repo.create(session, **data.category.model_dump())
                update_data["category_id"] = category.id
            else:
                update_data["category_id"] = None

        # 3. 포스트 기본 필드 업데이트
        await self.blog_post_repo.update(
            session,
            filters=[self.blog_post_repo.model.id == post_id],
            **update_data,
        )

        # 4. 태그 처리
        if "tags" in data.model_fields_set:
            # 새 태그 연결
            tag_ids = []
            for tag_dto in data.tags:
                tag = await self.tag_repo.get_by_name(session, tag_dto.name)
                if not tag:
                    tag = await self.tag_repo.create(session, **tag_dto.model_dump())
                tag_ids.append(tag.id)

            if tag_ids:
                post_tag_objects = [{"post_id": post_id, "tag_id": tag_id} for tag_id in tag_ids]
                await self.post_tag_repo.bulk_create(session, post_tag_objects)

    async def delete_post(
        self,
        user: get_current_user,
        session: postgres_session,
        post_id: int = Path(),
    ):
        await self.blog_post_repo.delete(session, post_id)
