from typing import Annotated, AsyncIterable

from fastapi import APIRouter, Depends, Path, status
from starlette.responses import StreamingResponse
from webtool.throttle import limiter

from src.app.fellows.api.dependencies import project_service
from src.app.fellows.schema.project import *
from src.core.dependencies.auth import get_current_user
from src.core.models.repository import PaginatedResult

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_project(
    project: Annotated[ERPNextProject, Depends(project_service.create_project)],
):
    """새로운 프로젝트를 생성합니다."""
    return project


@router.get("/", response_model=ProjectsPaginatedResponse)
async def get_projects(
    projects: Annotated[PaginatedResult, Depends(project_service.get_projects)],
):
    """자신의 프로젝트 전체를 조회합니다."""
    return projects


@router.get("/{project_id}", response_model=ERPNextProject)
async def get_project(
    project: Annotated[ERPNextProject, Depends(project_service.get_project)],
):
    """`project_id`로 프로젝트를 조회합니다"""
    return project


@router.put("/{project_id}", response_model=ERPNextProject)
async def update_project_info(
    updated_project: Annotated[ERPNextProject, Depends(project_service.update_project_info)],
):
    """`project_id`로 프로젝트를 업데이트합니다"""
    return updated_project


@router.put("/{project_id}/files", status_code=status.HTTP_204_NO_CONTENT)
async def add_files(
    _: Annotated[None, Depends(project_service.add_files)],
):
    pass


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    _: Annotated[None, Depends(project_service.delete_project)],
):
    """`project_id`로 프로젝트를 삭제합니다. (삭제 가능한 경우에만)"""
    pass


@limiter(1, 2)
@router.post("/{project_id}/submit")
async def submit_project(
    _: Annotated[None, Depends(project_service.submit_project)],
):
    pass


@router.post("/{project_id}/submit/cancel")
async def cancel_submit_project(
    _: Annotated[None, Depends(project_service.cancel_submit_project)],
):
    pass


@router.get("/{project_id}/tasks", response_model=ERPNextTaskPaginatedResponse)
async def get_tasks(
    tasks: Annotated[None, Depends(project_service.get_project_tasks)],
):
    return tasks


@limiter(max_requests=100, interval=60 * 60 * 24)
@router.get("/{project_id}/estimate", response_class=StreamingResponse)
async def estimate_stream(
    user: get_current_user,
    project_id: str = Path(),
):
    async def event_generator() -> AsyncIterable[str]:
        async for chunk in project_service.get_project_estimate(user, project_id):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@limiter(max_requests=500, interval=60 * 60 * 24)
@router.get("/estimate/feature", response_model=ProjectFeatureEstimateResponse)
async def feature_estimate(
    features: Annotated[list[str], Depends(project_service.get_project_feature_estimate)],
):
    return ProjectFeatureEstimateResponse(feature_list=features)
