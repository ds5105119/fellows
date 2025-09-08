from fastapi import Path

from src.app.fellows.repository.help import HelpRepository
from src.app.fellows.schema.help import HelpCreate, HelpsRead, HelpUpdate
from src.core.dependencies.db import db_session


class HelpService:
    def __init__(self, help_repository: HelpRepository):
        self.help_repository = help_repository

    async def get_helps(self, session: db_session) -> HelpsRead:
        helps = await self.help_repository.get_page(session, page=0, size=1000, filters=[])
        return HelpsRead.model_validate({"items": helps}, from_attributes=True)

    async def create_help(self, session: db_session, data: HelpCreate):
        await self.help_repository.create(session, **data.model_dump())

    async def update_help(self, session: db_session, data: HelpUpdate):
        await self.help_repository.update(session, **data.model_dump())

    async def delete_help(self, session: db_session, id: int = Path()):
        await self.help_repository.delete(session, id)
