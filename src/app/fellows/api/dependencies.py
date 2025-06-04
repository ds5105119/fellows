from src.app.fellows.model.project import Project, ProjectInfo
from src.app.fellows.repository.project import (
    ProjectInfoFileRecordLink,
    ProjectInfoFileRecordRepository,
    ProjectInfoRepository,
    ProjectRepository,
)
from src.app.fellows.service.project import ProjectService
from src.core.dependencies.infra import frappe_client, openai_client

project_repository = ProjectRepository(Project)
project_info_repository = ProjectInfoRepository(ProjectInfo)
project_info_file_record_repository = ProjectInfoFileRecordRepository(ProjectInfoFileRecordLink)
project_service = ProjectService(
    project_repository,
    project_info_repository,
    project_info_file_record_repository,
    openai_client,
    frappe_client,
)
