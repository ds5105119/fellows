import logging
import secrets
import uuid
from typing import Annotated

from fastapi import HTTPException, Path, Query, status
from keycloak import KeycloakAdmin
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import selectinload

from src.app.user.model.group import Group, GroupInvitation
from src.app.user.repository.group import (
    GroupInvitationRepository,
    GroupMembershipPositionLinkRepository,
    GroupMembershipRepository,
    GroupPositionRepository,
    GroupRepository,
)
from src.app.user.schema.group import *
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session

logger = logging.getLogger(__name__)


class GroupService:
    def __init__(
        self,
        group_repo: GroupRepository,
        membership_repo: GroupMembershipRepository,
        position_repo: GroupPositionRepository,
        invitation_repo: GroupInvitationRepository,
        link_repo: GroupMembershipPositionLinkRepository,
        keycloak_admin: KeycloakAdmin,
        develop_group_path: str = "/dev",
    ):
        self.develop_group_path = develop_group_path
        self.group_repo = group_repo
        self.membership_repo = membership_repo
        self.position_repo = position_repo
        self.invitation_repo = invitation_repo
        self.link_repo = link_repo
        self.keycloak_admin = keycloak_admin
        logger.info("GroupService initialized (DB-only).")

    async def _get_db_group_or_404(self, session: postgres_session, group_id: str) -> Group:
        db_group = await self.group_repo.get_group_by_id(session, group_id)
        if not db_group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group with ID '{group_id}' not found.")
        return db_group

    async def _get_user_role_in_group(self, session: postgres_session, group_id: str, user_sub: str) -> int:
        link = await self.link_repo.get_group_link_or_none(session, group_id, user_sub)
        return link.role if link else 4

    @staticmethod
    def _check_permission(
        user_app_role_in_group: int,
        required_action_role_field_value: int,
    ):
        if not required_action_role_field_value >= user_app_role_in_group:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    async def create_group(
        self,
        session: postgres_session,
        data: GroupCreateRequest,
        user: get_current_user,
    ) -> GroupResponse:
        if not any(group == self.develop_group_path for group in user.groups):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        if data.parent_id:
            parent_db_group = await self._get_db_group_or_404(session, data.parent_id)
            user_role_in_parent = await self._get_user_role_in_group(session, data.parent_id, user.sub)
            self._check_permission(user_role_in_parent, parent_db_group.role_create_sub_groups)

        try:
            # 그룹 생성
            new_group_id = str(uuid.uuid4())
            payload = data.model_dump(exclude_unset=True)
            db_group = await self.group_repo.create(
                session,
                id=new_group_id,
                created_by_sub=user.sub,
                **payload,
            )

            # 멤버쉽 생성
            user_membership_obj_instance = await self.membership_repo.get_instance(
                session, filters=[self.membership_repo.model.sub == user.sub]
            )
            user_membership_obj = user_membership_obj_instance.scalar_one_or_none()
            if not user_membership_obj:
                user_membership_obj = await self.membership_repo.create(session, sub=user.sub)

            # 링크 생성
            await self.link_repo.create(session, membership_sub=user.sub, group_id=new_group_id, role=0)

            logger.info(f"User {user.sub} created group {new_group_id} and became its owner.")
            return await self.get_group_by_id(session, user, new_group_id)

        except IntegrityError as e:
            await session.rollback()
            logger.error(f"DB integrity error creating group: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error creating group: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def get_group_by_id(
        self,
        session: postgres_session,
        user: get_current_user,
        group_id: str = Path(),
    ) -> GroupResponse:
        db_group = await self._get_db_group_or_404(session, group_id)
        user_role_in_group = await self._get_user_role_in_group(session, group_id, user.sub)
        self._check_permission(user_role_in_group, db_group.role_view_groups)

        group_instance = await self.group_repo.get_instance(
            session,
            filters=[Group.id == group_id],
            options=[
                selectinload(self.group_repo.model.memberships).selectinload(self.link_repo.model.position),
                selectinload(self.group_repo.model.memberships).selectinload(self.link_repo.model.membership),
                selectinload(self.group_repo.model.children),
                selectinload(self.group_repo.model.parent),
            ],
        )

        group = group_instance.scalar_one_or_none()
        group_response = GroupResponse.model_validate(group, from_attributes=True)

        return group_response

    async def get_groups(
        self,
        session: postgres_session,
        user: get_current_user,
        page: int = Query(0, ge=0),
        size: int = Query(20, ge=0, le=20),
        order_by: str = Query("name"),
        sort_desc: bool = Query(False),
        keyword: str | None = Query(None),
        group_type: str | None = Query(None),
    ) -> GroupsPaginatedResponse:
        filters = []
        if keyword:
            filters.append(self.group_repo.model.name.ilike(f"%{keyword}%"))
        if group_type:
            filters.append(self.group_repo.model.group_type == group_type)

        orderby = []
        if order_by and hasattr(self.group_repo.model, order_by):
            column_to_sort = getattr(self.group_repo.model, order_by)
            orderby.append(desc(column_to_sort) if sort_desc else column_to_sort)
        else:
            orderby.append(Group.name)

        result = await self.group_repo.get_groups_with_total(
            session,
            page,
            size,
            user,
            filters,
            orderby,
            [selectinload(self.group_repo.model.memberships).selectinload(self.link_repo.model.position)],
        )

        return GroupsPaginatedResponse.model_validate(result, from_attributes=True)

    async def update_group(
        self,
        session: postgres_session,
        user: get_current_user,
        data: GroupUpdateRequest,
        group: str = Path(),
    ) -> GroupResponse:
        db_group = await self._get_db_group_or_404(session, group)
        user_role_in_group = await self._get_user_role_in_group(session, group, user.sub)
        self._check_permission(user_role_in_group, db_group.role_edit_groups)

        update_payload = data.model_dump(exclude_unset=True)
        if not update_payload:
            return await self.get_group_by_id(session, user, group)

        # 부모 변경 시 권한 확인
        if data.parent_id and data.parent_id != db_group.parent_id:
            parent_db_group = await self._get_db_group_or_404(session, data.parent_id)
            user_role_in_new_parent = await self._get_user_role_in_group(session, data.parent_id, user.sub)
            self._check_permission(user_role_in_new_parent, parent_db_group.role_create_sub_groups)

        # 부모 삭제 금지
        elif data.parent_id is None and "parent_id" in data.model_fields_set and db_group.parent_id is not None:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

        try:
            await self.group_repo.update(session, filters=[self.group_repo.model.id == group], **update_payload)
            return await self.get_group_by_id(session, user, group)

        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating group {group}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def delete_group(
        self,
        session: postgres_session,
        user: get_current_user,
        delete_children: bool = Query(False),
        group: str = Path(),
    ) -> None:
        db_group = await self._get_db_group_or_404(session, group)
        user_role_in_group = await self._get_user_role_in_group(session, group, user.sub)
        if user_role_in_group != 0:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        if db_group.children and not delete_children:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        try:
            await self.group_repo.delete(session, id=group)
            logger.info(f"Group {group} and related data deleted from DB by user {user.sub}.")

        except NoResultFound:
            logger.warning(f"Group {group} not found during deletion by {user.sub}.")
            pass

        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting group {group} from DB: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # --- 멤버십 및 초대 관리 ---
    async def invite_member_to_group(
        self,
        session: postgres_session,
        user: get_current_user,
        data: GroupInvitationCreateRequest,
        group: str = Path(),
    ) -> GroupInvitationResponse:
        db_group = await self._get_db_group_or_404(session, group)
        user_role_in_group = await self._get_user_role_in_group(session, group, user.sub)
        self._check_permission(user_role_in_group, db_group.role_invite_groups)

        existing_invitation_instance = await self.invitation_repo.get_instance(
            session,
            filters=[
                self.invitation_repo.model.group_id == group,
                self.invitation_repo.model.invitee_email == user.email,
            ],
        )
        if existing_invitation_instance.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        token = secrets.token_urlsafe(64)
        role_to_assign_on_invite = data.role if data.role > 0 else 2

        try:
            invitation = await self.invitation_repo.create(
                session,
                group_id=group,
                inviter_sub=user.sub,
                inviter_email=user.email,
                invitee_email=data.invitee_email,
                role=role_to_assign_on_invite,
                token=token,
            )
            return GroupInvitationResponse.model_validate(invitation)

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def accept_group_invitation(
        self,
        session: postgres_session,
        user: get_current_user,
        token: Annotated[str, Query()],
    ) -> GroupResponse:
        invitation_instance = await self.invitation_repo.get_instance(
            session,
            filters=[GroupInvitation.token == token],
        )
        invitation = invitation_instance.scalar_one_or_none()

        if invitation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if invitation.invitee_email != user.email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        group_id = invitation.group_id
        role_to_assign = invitation.role or 2

        if not any(group == self.develop_group_path for group in user.groups):
            try:
                develop_group = self.keycloak_admin.get_group_by_path(self.develop_group_path)
                await self.keycloak_admin.a_group_user_add(user.sub, develop_group.get("group_id"))
            except Exception:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            await self.membership_repo.create(
                session,
                sub=user.sub,
                group_id=group_id,
                role=role_to_assign,
                joined_at=datetime.now(),
            )

            await self.invitation_repo.delete(session, id=invitation.id)
            return await self.get_group_by_id(session, user, group_id)

        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        except Exception as e:
            print(e)
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def update_group_member_details(
        self,
        session: postgres_session,
        user: get_current_user,
        data: GroupMembershipPositionLinkUpdateRequest,
        group: str = Path(),
        member: str = Path(),
    ) -> GroupResponse:
        db_group = await self._get_db_group_or_404(session, group)
        requester_link = await self.link_repo.get_group_link_or_none(session, group, user.sub)
        requester_role = requester_link.role if requester_link else 4

        if not user.sub == member:
            self._check_permission(requester_role, 1)

        target_membership = await self.link_repo.get_group_link_or_none(session, group, member)
        if not target_membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        update_data = data.model_dump(exclude_unset=True)

        # 역할 변경 시 특별 권한 확인
        if "role" in update_data and data.role != target_membership.role:
            if data.role == 0:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
            elif requester_role == 0 and user.sub == target_membership.membership_sub:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
            elif requester_role > 1 and target_membership.role > data.role:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        try:
            await self.link_repo.update(
                session,
                [
                    self.link_repo.model.group_id == group,
                    self.link_repo.model.membership_sub == member,
                ],
                role=data.role,
            )

            return await self.get_group_by_id(session, user, group)
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def remove_member_from_group(
        self,
        session: postgres_session,
        user: get_current_user,
        group: str = Path(),
        member: str = Path(),
    ):
        db_group = await self._get_db_group_or_404(session, group)
        requester_membership = await self._get_membership_or_none(session, group, user.sub)
        requester_role = requester_membership.role if requester_membership else 4

        target_membership = await self._get_membership_or_none(session, group, member)
        if not target_membership:
            return

        can_remove = False
        if requester_role == 0:
            if target_membership.role > 0:
                can_remove = True
            elif user.sub == member:
                pass
        elif requester_role == 1:
            if target_membership.role > 1:
                can_remove = True
        elif requester_role == 2:
            if target_membership.sub == user.sub:
                can_remove = True

        if not can_remove:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        try:
            await self.membership_repo.delete(session, target_membership.id)
            logger.info(f"Member {member} removed from group {group} by user {user.sub}.")
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def get_sent_invites(
        self,
        data: Annotated[GetInvitationsRequest, Query()],
        user: get_current_user,
        session: postgres_session,
    ) -> GroupInvitationsPaginatedResponse:
        result = await self.invitation_repo.get_page_with_total(
            session,
            data.page,
            data.size,
            [self.invitation_repo.model.inviter_sub == user.sub],
            orderby=[desc(self.invitation_repo.model.created_at)],
        )

        items = []
        if type(result.items) is not list:
            items = result.items.scalars().all()

        return GroupInvitationsPaginatedResponse.model_validate(
            {"total": result.total, "items": items},
            from_attributes=True,
        )

    async def get_received_invites(
        self,
        data: Annotated[GetInvitationsRequest, Query()],
        user: get_current_user,
        session: postgres_session,
    ) -> GroupInvitationsPaginatedResponse:
        result = await self.invitation_repo.get_page_with_total(
            session,
            data.page,
            data.size,
            [self.invitation_repo.model.invitee_email == user.email],
            orderby=[desc(self.invitation_repo.model.created_at)],
        )

        items = []
        if type(result.items) is not list:
            items = result.items.scalars().all()

        return GroupInvitationsPaginatedResponse.model_validate(
            {"total": result.total, "items": items},
            from_attributes=True,
        )

    async def delete_sent_invite(
        self,
        user: get_current_user,
        session: postgres_session,
        token: Annotated[str, Query()],
    ):
        result = await self.invitation_repo.get(
            session,
            [self.invitation_repo.model.inviter_sub == user.sub],
            [self.invitation_repo.model.token],
        )
        invite_token = result.scalar_one_or_none()

        if invite_token != token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await self.invitation_repo.delete_by_token(session, token)

    async def delete_receive_invite(
        self,
        user: get_current_user,
        session: postgres_session,
        token: Annotated[str, Query()],
    ):
        result = await self.invitation_repo.get(
            session,
            [self.invitation_repo.model.invitee_email == user.email],
            [self.invitation_repo.model.token],
        )
        invite_token = result.scalar_one_or_none()

        if invite_token != token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await self.invitation_repo.delete_by_token(session, token)
