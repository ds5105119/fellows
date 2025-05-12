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
    pass


class FileRecordRepository(
    FileRecordCreateRepository, FileRecordReadRecordRepository, FileRecordUpdateRepository, FileRecordDeleteRepository
):
    pass
