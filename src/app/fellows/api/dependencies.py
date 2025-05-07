from src.app.fellows.model.project import Project, ProjectGroupLink, ProjectInfo
from src.app.fellows.repository.project import ProjectGroupLinkRepository, ProjectInfoRepository, ProjectRepository
from src.app.fellows.service.project import ProjectService
from src.core.dependencies.infra import client

project_repository = ProjectRepository(Project)
project_info_repository = ProjectInfoRepository(ProjectInfo)
project_group_link_repository = ProjectGroupLinkRepository(ProjectGroupLink)
project_service = ProjectService(project_repository, project_info_repository, client)
