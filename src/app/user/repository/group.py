from typing import cast

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.user.model.group import GroupInvitation
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class GroupInvitationCreateRepository(ABaseCreateRepository[GroupInvitation]):
    pass


class GroupInvitationReadRepository(ABaseReadRepository[GroupInvitation]):
    pass


class GroupInvitationUpdateRepository(ABaseUpdateRepository[GroupInvitation]):
    pass


class GroupInvitationDeleteRepository(ABaseDeleteRepository[GroupInvitation]):
    async def _delete_by_token(self, session: AsyncSession, token: str) -> None:
        stmt = delete(self.model).where(cast("ColumnElement[bool]", self.model.token == token))
        await session.execute(stmt)
        await session.commit()

    async def _bulk_delete_by_token(self, session: AsyncSession, tokens: list[str]) -> None:
        stmt = delete(self.model).where(cast("ColumnElement[bool]", self.model.token.in_(tokens)))
        await session.execute(stmt)
        await session.commit()

    async def delete_by_token(self, session: AsyncSession, token: str | tuple[str] | list[str]) -> None:
        if isinstance(token, str):
            await self._delete_by_token(session, token)
        elif isinstance(token, (tuple, list)) and len(token):
            await self._bulk_delete_by_token(session, list(token))
        else:
            raise ValueError("'token' must be an str, or Iterable of str")

    async def _delete_by_group_id(self, session: AsyncSession, group_id: str) -> None:
        stmt = delete(self.model).where(cast("ColumnElement[bool]", self.model.group_id == group_id))
        await session.execute(stmt)
        await session.commit()

    async def _bulk_delete_by_group_id(self, session: AsyncSession, group_ids: list[str]) -> None:
        stmt = delete(self.model).where(cast("ColumnElement[bool]", self.model.group_id.in_(group_ids)))
        await session.execute(stmt)
        await session.commit()

    async def delete_by_group_id(self, session: AsyncSession, group_id: str | tuple[str] | list[str]) -> None:
        if isinstance(group_id, str):
            await self._delete_by_group_id(session, group_id)
        elif isinstance(group_id, (tuple, list)) and len(group_id):
            await self._bulk_delete_by_group_id(session, list(group_id))
        else:
            raise ValueError("'token' must be an str, or Iterable of str")


class GroupInvitationRepository(
    GroupInvitationCreateRepository,
    GroupInvitationReadRepository,
    GroupInvitationUpdateRepository,
    GroupInvitationDeleteRepository,
):
    pass
