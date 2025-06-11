from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.app.blog.api.dependencies import blog_service
from src.app.blog.schema.blog import *

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_post(
    post: Annotated[BlogPostWithNestedDto, Depends(blog_service.create_blog_post)],
):
    return post


@router.get("/{post_id}", response_model=BlogPostWithNestedDto)
async def get_post(
    posts: Annotated[BlogPostWithNestedDto, Depends(blog_service.get_post_by_id)],
):
    return posts


@router.get("", response_model=BlogPostPaginatedResponse)
async def get_posts(
    post: Annotated[BlogPostPaginatedResponse, Depends(blog_service.get_posts)],
):
    return post


@router.put("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_post(
    _: Annotated[None, Depends(blog_service.update_post)],
):
    pass


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    _: Annotated[None, Depends(blog_service.delete_post)],
):
    pass
