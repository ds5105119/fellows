from src.app.fellows.model.project import Project, ProjectGroups, ProjectInfo
from src.app.fellows.repository.project import (
    ProjectGroupsRepository,
    ProjectInfoFileRecordRepository,
    ProjectInfoFileRecords,
    ProjectInfoRepository,
    ProjectRepository,
)
from src.app.fellows.service.project import ProjectService
from src.core.dependencies.infra import client

project_repository = ProjectRepository(Project)
project_info_repository = ProjectInfoRepository(ProjectInfo)
project_group_repository = ProjectGroupsRepository(ProjectGroups)
project_info_file_record_repository = ProjectInfoFileRecordRepository(ProjectInfoFileRecords)
project_service = ProjectService(
    project_repository,
    project_info_repository,
    project_info_file_record_repository,
    client,
)
