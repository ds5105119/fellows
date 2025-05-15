from typing import Annotated, AsyncIterable

from fastapi import APIRouter, Depends, Path, status
from starlette.responses import StreamingResponse
from webtool.throttle import limiter

from src.app.fellows.api.dependencies import project_service
from src.app.fellows.model.project import Project
from src.app.fellows.schema.project import ProjectFeatureEstimateResponse, ProjectFileRecordsSchema, ProjectSchema
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session
from src.core.models.repository import PaginatedResult

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_project(
    project: Annotated[Project, Depends(project_service.create_project)],
):
    """새로운 프로젝트를 생성합니다."""
    return ProjectSchema.model_validate(project)


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project: Annotated[Project, Depends(project_service.get_project)],
):
    """`project_id`로 프로젝트를 조회합니다"""
    return ProjectSchema.model_validate(project)


@router.get("/", response_model=PaginatedResult[ProjectSchema])
async def get_projects(
    result: Annotated[PaginatedResult, Depends(project_service.get_projects)],
):
    """자신의 프로젝트 전체를 조회합니다."""
    if result.total:
        result.items = [ProjectSchema.model_validate(project) for project in result.items]
    return result


@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project_info(
    updated_project: Annotated[ProjectSchema, Depends(project_service.update_project_info)],
):
    """`project_id`로 프로젝트를 업데이트합니다"""
    return updated_project


@router.post("/{project_id}/files")
async def add_files_to_project(
    updated_project: Annotated[ProjectSchema, Depends(project_service.add_file_to_project)],
):
    """`project_id`로 프로젝트에 파일을 추가합니다"""
    return updated_project


@router.delete("/{project_id}")
async def delete_project(
    _: Annotated[None, Depends(project_service.delete_project)],
):
    """`project_id`로 프로젝트를 삭제합니다. (삭제 가능한 경우에만)"""
    pass


@limiter(max_requests=200, interval=60 * 60 * 24)
@router.get("/estimate/feature", response_model=ProjectFeatureEstimateResponse)
async def feature_estimate(
    features: Annotated[list[str], Depends(project_service.get_project_feature_estimate)],
):
    return ProjectFeatureEstimateResponse(feature_list=features)


@limiter(max_requests=100, interval=60 * 60 * 24)
@router.get("/estimate/project/{project_id}", response_class=StreamingResponse)
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
