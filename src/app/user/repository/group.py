from typing import Sequence, cast

from sqlalchemy import ColumnElement, and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.sql.base import ExecutableOption

from src.app.user.model.group import (
    Group,
    GroupInvitation,
    GroupMembership,
    GroupMembershipPositionLink,
    GroupPosition,
    GroupSchedule,
)
from src.core.dependencies.auth import User
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
    PaginatedResult,
)


class GroupCreateRepository(ABaseCreateRepository[Group]):
    pass


class GroupReadRepository(ABaseReadRepository[Group]):
    async def get_group_by_id(self, session: AsyncSession, group_id: str) -> Group:
        db_group_instance = await self.get_instance(
            session,
            filters=[
                self.model.id == group_id,
            ],
        )
        return db_group_instance.scalar_one_or_none()

    async def get_groups_with_total(
        self,
        session: AsyncSession,
        page: int,
        size: int,
        user: User,
        filters: Sequence,
        orderby: Sequence[ColumnElement] | None = None,
        options: Sequence[ExecutableOption] = None,
    ) -> PaginatedResult[Group]:
        GUEST_ROLE_VALUE = 3
        UserLink = aliased(GroupMembershipPositionLink, name="user_link")

        permission_filter = or_(
            self.model.role_view_groups >= GUEST_ROLE_VALUE,
            and_(
                UserLink.membership_sub == user.sub,
                UserLink.role <= self.model.role_view_groups,
            ),
        )

        # 최종 필터 목록
        all_filters = list(filters)
        all_filters.append(permission_filter)

        # Count 쿼리
        count_stmt = (
            select(func.count(self.model.id))
            .select_from(self.model)
            .outerjoin(
                UserLink,
                and_(
                    self.model.id == UserLink.group_id,
                    UserLink.membership_sub == user.sub,
                ),
            )
            .where(and_(*all_filters))
        )
        total_count_result = await session.execute(count_stmt)
        total = total_count_result.scalar_one_or_none() or 0

        if total == 0:
            return PaginatedResult(total=0, items=[])

        # Items 쿼리
        items_stmt = (
            select(self.model)
            .select_from(self.model)
            .outerjoin(UserLink, and_(self.model.id == UserLink.group_id, UserLink.membership_sub == user.sub))
            .where(and_(*all_filters))
        )

        if orderby:
            items_stmt = items_stmt.order_by(*orderby)
        else:
            items_stmt = items_stmt.order_by(self.model.name)

        items_stmt = items_stmt.limit(size).offset(page * size)

        if options:
            items_stmt = items_stmt.options(*options)

        items_result = await session.execute(items_stmt)
        items = items_result.scalars().unique().all()

        return PaginatedResult(total, items)


class GroupUpdateRepository(ABaseUpdateRepository[Group]):
    pass


class GroupDeleteRepository(ABaseDeleteRepository[Group]):
    pass


class GroupMembershipCreateRepository(ABaseCreateRepository[GroupMembership]):
    pass


class GroupMembershipReadRepository(ABaseReadRepository[GroupMembership]):
    pass


class GroupMembershipUpdateRepository(ABaseUpdateRepository[GroupMembership]):
    pass


class GroupMembershipDeleteRepository(ABaseDeleteRepository[GroupMembership]):
    pass


class GroupMembershipPositionLinkCreateRepository(ABaseCreateRepository[GroupMembershipPositionLink]):
    pass


class GroupMembershipPositionLinkReadRepository(ABaseReadRepository[GroupMembershipPositionLink]):
    async def get_group_link_or_none(
        self, session: AsyncSession, group_id: str, user_sub: str
    ) -> GroupMembershipPositionLink | None:
        link_instance = await self.get_instance(
            session,
            filters=[
                self.model.group_id == group_id,
                self.model.membership_sub == user_sub,
            ],
            options=[selectinload(self.model.position)],
        )
        return link_instance.scalar_one_or_none()


class GroupMembershipPositionLinkUpdateRepository(ABaseUpdateRepository[GroupMembershipPositionLink]):
    pass


class GroupMembershipPositionLinkDeleteRepository(ABaseDeleteRepository[GroupMembershipPositionLink]):
    pass


class GroupPositionCreateRepository(ABaseCreateRepository[GroupPosition]):
    pass


class GroupPositionReadRepository(ABaseReadRepository[GroupPosition]):
    pass


class GroupPositionUpdateRepository(ABaseUpdateRepository[GroupPosition]):
    pass


class GroupPositionDeleteRepository(ABaseDeleteRepository[GroupPosition]):
    pass


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


class GroupRepository(
    GroupCreateRepository,
    GroupReadRepository,
    GroupUpdateRepository,
    GroupDeleteRepository,
):
    pass


class GroupMembershipRepository(
    GroupMembershipCreateRepository,
    GroupMembershipReadRepository,
    GroupMembershipUpdateRepository,
    GroupMembershipDeleteRepository,
):
    pass


class GroupMembershipPositionLinkRepository(
    GroupMembershipPositionLinkCreateRepository,
    GroupMembershipPositionLinkReadRepository,
    GroupMembershipPositionLinkUpdateRepository,
    GroupMembershipPositionLinkDeleteRepository,
):
    pass


class GroupPositionRepository(
    GroupPositionCreateRepository,
    GroupPositionReadRepository,
    GroupPositionUpdateRepository,
    GroupPositionDeleteRepository,
):
    pass


class GroupInvitationRepository(
    GroupInvitationCreateRepository,
    GroupInvitationReadRepository,
    GroupInvitationUpdateRepository,
    GroupInvitationDeleteRepository,
):
    pass
