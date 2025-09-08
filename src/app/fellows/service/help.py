from uuid import uuid4

from fastapi import HTTPException, Path, status

from src.app.fellows.repository.help import HelpRepository
from src.app.fellows.schema.help import HelpCreate, HelpsRead, HelpUpdate
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import db_session


class HelpService:
    def __init__(self, help_repository: HelpRepository):
        self.help_repository = help_repository

    async def get_helps(self, session: db_session) -> HelpsRead:
        helps = await self.help_repository.get_page(session, page=0, size=1000, filters=[])
        return HelpsRead.model_validate({"items": helps}, from_attributes=True)

    async def create_help(self, session: db_session, data: HelpCreate, user: get_current_user):
        if "/manager" not in user.groups:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await self.help_repository.create(session, **data.model_dump(), id=uuid4())

    async def update_help(self, session: db_session, data: HelpUpdate, user: get_current_user, id: int = Path()):
        if "/manager" not in user.groups:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await self.help_repository.update(session, filters=[self.help_repository.model.id == id], **data.model_dump())

    async def delete_help(self, session: db_session, user: get_current_user, id: int = Path()):
        if "/manager" not in user.groups:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await self.help_repository.delete(session, id)
