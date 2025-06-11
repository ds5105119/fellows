from src.app.blog.model.blog import *
from src.app.blog.repository.blog import (
    AuthorRepository,
    BlogPostRepository,
    CategoryRepository,
    PostTagRepository,
    TagRepository,
)
from src.app.blog.service.blog import BlogService

author_repository = AuthorRepository(Author)
blog_post_repository = BlogPostRepository(BlogPost)
category_repository = CategoryRepository(Category)
post_tag_repository = PostTagRepository(PostTag)
tag_repository = TagRepository(Tag)

blog_service = BlogService(
    author_repository, blog_post_repository, category_repository, post_tag_repository, tag_repository
)
