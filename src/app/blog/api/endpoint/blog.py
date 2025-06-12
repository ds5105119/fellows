from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.app.blog.api.dependencies import blog_service
from src.app.blog.schema.blog import *

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_post(
    post: Annotated[BlogPostDto, Depends(blog_service.create_blog_post)],
):
    return post


@router.get("/path", response_model=list[str])
async def post_paths(
    paths: Annotated[list[str], Depends(blog_service.post_paths)],
):
    return paths


@router.get("/{post_id}", response_model=BlogPostDto)
async def get_post(
    posts: Annotated[BlogPostDto, Depends(blog_service.get_post_by_id)],
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
