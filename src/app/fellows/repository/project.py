from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.fellows.model.project import Project, ProjectInfo, ProjectInfoFileRecordLink
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


class ProjectInfoFileRecordCreateRepository(ABaseCreateRepository[ProjectInfoFileRecordLink]):
    pass


class ProjectInfoFileRecordReadRepository(ABaseReadRepository[ProjectInfoFileRecordLink]):
    pass


class ProjectInfoFileRecordUpdateRepository(ABaseUpdateRepository[ProjectInfoFileRecordLink]):
    pass


class ProjectInfoFileRecordDeleteRepository(ABaseDeleteRepository[ProjectInfoFileRecordLink]):
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


class ProjectInfoFileRecordRepository(
    ProjectInfoFileRecordCreateRepository,
    ProjectInfoFileRecordReadRepository,
    ProjectInfoFileRecordUpdateRepository,
    ProjectInfoFileRecordDeleteRepository,
):
    pass
