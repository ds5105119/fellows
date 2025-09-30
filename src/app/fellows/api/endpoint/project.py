from typing import Annotated, AsyncIterable

from fastapi import APIRouter, Depends, Path, status
from starlette.responses import StreamingResponse
from webtool.throttle import limiter

from src.app.fellows.api.dependencies import contract_service, project_service, report_service
from src.app.fellows.schema.contract import ERPNextContractPaginatedResponse, UserERPNextContract
from src.app.fellows.schema.project import *
from src.app.fellows.schema.report import ReportResponse
from src.app.user.schema.user_data import ProjectAdminUserAttributes
from src.core.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/contract", response_model=ERPNextContractPaginatedResponse)
async def get_contracts(
    contracts: Annotated[ERPNextContractPaginatedResponse, Depends(contract_service.get_contracts)],
):
    return contracts


@router.get("/contract/{contract_id}", response_model=UserERPNextContract)
async def get_contract(
    contract: Annotated[UserERPNextContract, Depends(contract_service.get_contract)],
):
    return contract


@router.put("/contract/{contract_id}", response_model=UserERPNextContract)
async def update_contract(
    contract: Annotated[UserERPNextContract, Depends(contract_service.update_contracts)],
):
    return contract


@router.post("/contract/callback/new")
async def new_contract_callback(_: Annotated[None, Depends(contract_service.new_contract_callback)]):
    return None


@router.get("/task", response_model=ERPNextTaskPaginatedResponse)
async def get_tasks(tasks: Annotated[ERPNextTaskPaginatedResponse, Depends(project_service.read_tasks)]):
    return tasks


@limiter(1, 2)
@router.post("/issue", response_model=ERPNextIssue)
async def create_issue(issue: Annotated[ERPNextIssue, Depends(project_service.create_issue)]):
    return issue


@router.get("/issue", response_model=ERPNextIssuePaginatedResponse)
async def get_issues(
    issues: Annotated[ERPNextIssuePaginatedResponse, Depends(project_service.read_issues)],
):
    return issues


@limiter(1, 2)
@router.put("/issue/{name}", response_model=ERPNextIssue)
async def update_issue(issue: Annotated[ERPNextIssue, Depends(project_service.update_issue)]):
    return issue


@limiter(1, 2)
@router.delete("/issue/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(_: Annotated[None, Depends(project_service.delete_issue)]):
    pass


@limiter(1, 2)
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    project: Annotated[ERPNextProject, Depends(project_service.create_project)],
):
    """새로운 프로젝트를 생성합니다."""
    return project


@router.get("", response_model=ProjectsPaginatedResponse)
async def get_projects(
    projects: Annotated[ProjectsPaginatedResponse, Depends(project_service.get_projects)],
):
    """자신의 프로젝트 전체를 조회합니다."""
    return projects


@router.get("/overview", response_model=OverviewProjectsPaginatedResponse)
async def get_project_overview(
    projects: Annotated[OverviewProjectsPaginatedResponse, Depends(project_service.get_projects_overview)],
):
    return projects


@router.get("/{project_id}/customer", response_model=ProjectAdminUserAttributes)
async def get_project_customer(
    customer: Annotated[ProjectAdminUserAttributes, Depends(project_service.get_project_admin)],
):
    return customer


@router.get("/{project_id}", response_model=ERPNextProjectForUser)
async def get_project(
    project: Annotated[ERPNextProjectForUser, Depends(project_service.get_project)],
):
    """`project_id`로 프로젝트를 조회합니다"""
    return project


@limiter(1, 2)
@router.post("/{project_id}/group/invite", status_code=status.HTTP_204_NO_CONTENT)
async def invite_user_to_project(
    project: Annotated[None, Depends(project_service.add_members_to_project)],
):
    """`project_id`로 팀원을 초대합니다"""
    return project


@limiter(1, 2)
@router.post("/{project_id}/group/invite/accept", response_model=ERPNextProject)
async def accept_invite_to_project(
    project: Annotated[ERPNextProject, Depends(project_service.accept_invite_to_project)],
):
    """`project_id`로 초대를 수락합니다"""
    return project


@limiter(1, 2)
@router.put("/{project_id}/group", response_model=ERPNextProject)
async def update_project_team(
    project: Annotated[ERPNextProject, Depends(project_service.update_project_team)],
):
    """`project_id`로 팀원을 초대합니다"""
    return project


@limiter(1, 2)
@router.put("/{project_id}", response_model=ERPNextProject)
async def update_project(
    project: Annotated[ERPNextProject, Depends(project_service.update_project_info)],
):
    """`project_id`로 프로젝트를 업데이트합니다"""
    return project


@limiter(1, 2)
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


@router.get("/slots/quote", response_model=list[QuoteSlot])
async def get_quote_slots(
    slots: Annotated[None, Depends(project_service.get_quote_slots)],
):
    return slots


@limiter(1, 2)
@router.post("/{project_id}/files", status_code=status.HTTP_204_NO_CONTENT)
async def create_files(_: Annotated[None, Depends(project_service.create_file)]):
    pass


@router.get("/{project_id}/files/{key}", response_model=ERPNextFile)
async def get_file(file: Annotated[ERPNextFile, Depends(project_service.read_file)]):
    return file


@router.get("/{project_id}/files", response_model=ERPNextFilesResponse)
async def get_files(files: Annotated[ERPNextFilesResponse, Depends(project_service.read_files)]):
    return files


@limiter(1, 2)
@router.delete("/{project_id}/files/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_files(_: Annotated[None, Depends(project_service.delete_file)]):
    pass


@router.get("/{project_id}/report/daily", response_model=ReportResponse)
async def get_daily_report(report: Annotated[ReportResponse, Depends(report_service.get_daily_report)]):
    return report


@router.get("/{project_id}/report/monthly", response_model=ReportResponse)
async def get_daily_report(report: Annotated[ReportResponse, Depends(report_service.get_monthly_report)]):
    return report


@router.get("/{project_id}/estimate/status", response_model=bool)
async def estimate_stream_status(s: Annotated[bool, Depends(project_service.get_project_estimate_status)]):
    return s


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
async def estimate_feature(
    features: Annotated[list[str], Depends(project_service.get_project_feature_estimate)],
):
    return ProjectFeatureEstimateResponse(feature_list=features)


@limiter(max_requests=500, interval=60 * 60 * 24)
@router.get("/estimate/info", response_model=ProjectSummary2InfoResponse)
async def estimate_title(
    info: Annotated[ProjectSummary2InfoResponse, Depends(project_service.generate_project_info_by_summary)],
):
    return info


@router.get("/estimate/report/{report_id}/status", response_model=bool)
async def estimate_report_status(s: Annotated[bool, Depends(report_service.get_report_summary_status)]):
    return s


@limiter(max_requests=100, interval=60 * 60 * 24)
@router.get("/estimate/report/{report_id}", response_model=ReportResponse)
async def estimate_report_summary(
    report: Annotated[ReportResponse, Depends(report_service.get_report_summary)],
):
    return report
