from src.app.fellows.model.project import Project, ProjectGroupLink, ProjectInfo
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class ProjectReadRepository(ABaseReadRepository[Project]):
    pass


class ProjectCreateRepository(ABaseCreateRepository[Project]):
    pass


class ProjectUpdateRepository(ABaseUpdateRepository[Project]):
    pass


class ProjectDeleteRepository(ABaseDeleteRepository[Project]):
    pass


class ProjectInfoCreateRepository(ABaseCreateRepository[ProjectInfo]):
    pass


class ProjectInfoReadRepository(ABaseReadRepository[ProjectInfo]):
    pass


class ProjectInfoUpdateRepository(ABaseUpdateRepository[ProjectInfo]):
    pass


class ProjectInfoDeleteRepository(ABaseDeleteRepository[ProjectInfo]):
    pass


class ProjectGroupLinkCreateRepository(ABaseCreateRepository[ProjectGroupLink]):
    pass


class ProjectGroupLinkReadRepository(ABaseReadRepository[ProjectGroupLink]):
    pass


class ProjectGroupLinkUpdateRepository(ABaseUpdateRepository[ProjectGroupLink]):
    pass


class ProjectGroupLinkDeleteRepository(ABaseDeleteRepository[ProjectGroupLink]):
    pass


class ProjectRepository(
    ProjectCreateRepository,
    ProjectReadRepository,
    ProjectUpdateRepository,
    ProjectDeleteRepository,
):
    pass


class ProjectInfoRepository(
    ProjectInfoCreateRepository,
    ProjectInfoReadRepository,
    ProjectInfoUpdateRepository,
    ProjectInfoDeleteRepository,
):
    pass


class ProjectGroupLinkRepository(
    ProjectGroupLinkCreateRepository,
    ProjectGroupLinkReadRepository,
    ProjectGroupLinkUpdateRepository,
    ProjectGroupLinkDeleteRepository,
):
    pass
