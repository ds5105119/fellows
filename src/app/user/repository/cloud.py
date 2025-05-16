from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.user.model.cloud import FileRecord
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class FileRecordCreateRepository(ABaseCreateRepository[FileRecord]):
    pass


class FileRecordReadRecordRepository(ABaseReadRepository[FileRecord]):
    pass


class FileRecordUpdateRepository(ABaseUpdateRepository[FileRecord]):
    pass


class FileRecordDeleteRepository(ABaseDeleteRepository[FileRecord]):
    async def _delete_by_key(self, session: AsyncSession, key: str) -> None:
        stmt = delete(self.model).where(self.model.key == key)
        await session.execute(stmt)
        await session.commit()

    async def _bulk_delete_by_key(self, session: AsyncSession, keys: list[str]) -> None:
        stmt = delete(self.model).where(self.model.key.in_(keys))
        await session.execute(stmt)
        await session.commit()

    async def delete_by_key(self, session: AsyncSession, key: str | tuple[str] | list[str]) -> None:
        if isinstance(key, (int, str)):
            await self._delete_by_key(session, key)
        elif isinstance(key, (tuple, list)) and len(key):
            await self._bulk_delete_by_key(session, list(key))
        else:
            raise ValueError("'key' must be an str, or Iterable of str")


class FileRecordRepository(
    FileRecordCreateRepository, FileRecordReadRecordRepository, FileRecordUpdateRepository, FileRecordDeleteRepository
):
    pass
