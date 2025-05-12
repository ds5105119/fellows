from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.fellows.model.project import Project, ProjectGroups, ProjectInfo, ProjectInfoFileRecords
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
    async def delete_by_project_id_sub(self, session: AsyncSession, project_id: str, sub: str) -> None:
        stmt = delete(self.model).where(
            self.model.project_id == project_id,
            self.model.sub == sub,
            self.model.deletable == True,
        )
        await session.execute(stmt)
        await session.commit()


class ProjectInfoCreateRepository(ABaseCreateRepository[ProjectInfo]):
    pass


class ProjectInfoReadRepository(ABaseReadRepository[ProjectInfo]):
    pass


class ProjectInfoUpdateRepository(ABaseUpdateRepository[ProjectInfo]):
    pass


class ProjectInfoDeleteRepository(ABaseDeleteRepository[ProjectInfo]):
    pass


class ProjectGroupsCreateRepository(ABaseCreateRepository[ProjectGroups]):
    pass


class ProjectGroupsReadRepository(ABaseReadRepository[ProjectGroups]):
    pass


class ProjectGroupsUpdateRepository(ABaseUpdateRepository[ProjectGroups]):
    pass


class ProjectGroupsDeleteRepository(ABaseDeleteRepository[ProjectGroups]):
    pass


class ProjectInfoFileRecordCreateRepository(ABaseCreateRepository[ProjectInfoFileRecords]):
    pass


class ProjectInfoFileRecordReadRepository(ABaseReadRepository[ProjectInfoFileRecords]):
    pass


class ProjectInfoFileRecordUpdateRepository(ABaseUpdateRepository[ProjectInfoFileRecords]):
    pass


class ProjectInfoFileRecordDeleteRepository(ABaseDeleteRepository[ProjectInfoFileRecords]):
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


class ProjectGroupsRepository(
    ProjectGroupsCreateRepository,
    ProjectGroupsReadRepository,
    ProjectGroupsUpdateRepository,
    ProjectGroupsDeleteRepository,
):
    pass


class ProjectInfoFileRecordRepository(
    ProjectInfoFileRecordCreateRepository,
    ProjectInfoFileRecordReadRepository,
    ProjectInfoFileRecordUpdateRepository,
    ProjectInfoFileRecordDeleteRepository,
):
    pass
