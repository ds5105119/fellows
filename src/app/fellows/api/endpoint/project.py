from typing import Annotated, Any, AsyncIterable

from fastapi import APIRouter, Depends, Path, status
from starlette.responses import StreamingResponse
from webtool.throttle import limiter

from src.app.fellows.api.dependencies import project_service
from src.app.fellows.model.project import Project
from src.app.fellows.schema.project import ProjectSchema
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_project(
    _: Annotated[Project, Depends(project_service.create_project)],
):
    """새로운 프로젝트를 생성합니다."""
    pass


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project: Annotated[Project, Depends(project_service.get_project)],
):
    """`project_id`로 프로젝트를 조회합니다"""
    return ProjectSchema.model_validate(project)


@router.get("/", response_model=list[ProjectSchema])
async def get_projects(
    projects: Annotated[list[dict[str, Any]], Depends(project_service.get_projects)],
):
    """자신의 프로젝트 전체를 조회합니다."""

    return [ProjectSchema.model_validate(project) for project in projects]


@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project(
    updated_project: Annotated[ProjectSchema, Depends(project_service.update_project)],
):
    """`project_id`로 프로젝트를 업데이트합니다"""
    return updated_project


@limiter(max_requests=50)
@router.get("/estimate/{project_id}", response_class=StreamingResponse)
async def estimate_stream(
    user: get_current_user,
    session: postgres_session,
    project_id: str = Path(),
):
    async def event_generator() -> AsyncIterable[str]:
        async for chunk in project_service.get_project_estimate(user, session, project_id):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
