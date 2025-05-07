import logging
import secrets
from typing import Annotated, Any, Dict, List, Optional

from fastapi import HTTPException, Path, Query, status
from keycloak import KeycloakAdmin
from keycloak.exceptions import (
    KeycloakDeleteError,
    KeycloakGetError,
    KeycloakPostError,
    KeycloakPutError,
)
from sqlalchemy import desc

from src.app.user.model.group import GroupInvitation
from src.app.user.repository.group import GroupInvitationRepository
from src.app.user.schema.group import (
    GetInvitationsRequest,
    GroupInvitationCreate,
    GroupRepresentation,
    GroupRequest,
    GroupUpdateRequest,
)
from src.core.dependencies.auth import User, get_current_user
from src.core.dependencies.db import postgres_session

logger = logging.getLogger(__name__)


async def _get_user_by_email_safe(keycloak_admin: KeycloakAdmin, email: str) -> Optional[Dict[str, Any]]:
    """Safely get user representation by email, returning None if not found."""
    try:
        users = await keycloak_admin.a_get_users(query={"email": email, "exact": "true"})
        if not users:
            return None
        return users[0]
    except KeycloakGetError:
        return None


async def _get_group_safe(keycloak_admin: KeycloakAdmin, group_id: str) -> Optional[Dict[str, Any]]:
    try:
        group = await keycloak_admin.a_get_group(group_id=group_id, full_hierarchy=False)
        return group
    except KeycloakGetError:
        return None


class GroupService:
    """
    Keycloak 그룹 관리 및 사용자 초대 기능을 제공하는 서비스 클래스.
    역할(owner, admin, member)은 그룹 속성을 통해 관리됩니다.
    """

    def __init__(
        self,
        invitation_repository: GroupInvitationRepository,
        keycloak_admin: KeycloakAdmin,
    ):
        """
        서비스 초기화. KeycloakAdmin 클라이언트와 GroupInvitationRepository를 주입받습니다.
        """
        self.invitation_repository = invitation_repository
        self.keycloak_admin = keycloak_admin

    async def _get_group_and_check_permission(
        self,
        group_id: str,
        user: User,
        allowed_roles: List[str],
    ) -> Dict[str, Any]:
        """
        그룹 정보를 가져오고 현재 사용자의 권한(역할)을 확인합니다.
        그룹이 없거나 사용자에게 필요한 역할이 없으면 HTTPException을 발생시킵니다.

        Args:
            allowed_roles: ["owner"], ["owner", "admin"], ["owner", "admin", "member"]
        """
        # 그룹 조회
        group = await _get_group_safe(self.keycloak_admin, group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group with not found.",
            )

        # 멤버 목록 조회
        try:
            group_members = await self.keycloak_admin.a_get_group_members(
                group_id=group_id,
                query={"briefRepresentation": "true"},
            )
            is_member = any(member["id"] == user.sub for member in group_members)
        except KeycloakGetError:
            logger.warning(f"Failed to retrieve members for group {group_id} during permission check.")
            is_member = False

        # 그룹 역할 정보 추출
        attributes = group.get("attributes", {})
        owner_sub = attributes.get("owner", [None])[0]
        admin_subs = attributes.get("admins", [])

        # 사용자 역할 결정
        user_role = "guest"
        if user.sub == owner_sub:
            user_role = "owner"
        elif user.sub in admin_subs:
            user_role = "admin"
        elif is_member:
            user_role = "member"

        # 권한 확인
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role(s): {', '.join(allowed_roles)}. Your role: {user_role}.",
            )

        # 그룹 정보에 현재 사용자 역할 추가 반환
        group["current_user_role"] = user_role
        return group

    async def _add_admin_role_internal(self, group_id: str, user_id: str) -> None:
        """
        내부 사용 목적: 사용자에게 admin 역할을 부여합니다. 권한 검사는 하지 않습니다.
        """
        # 그룹 조회
        group = await _get_group_safe(self.keycloak_admin, group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group with not found.",
            )

        attributes = group.get("attributes", {})
        owner_sub = attributes.get("owner", [None])[0]
        admins_list = attributes.get("admins", [])

        # 역할 확인
        if user_id == owner_sub:
            return
        if user_id in admins_list:
            return

        # 관리자 추가
        admins_list.append(user_id)
        attributes["admins"] = admins_list
        payload = {"attributes": attributes}
        await self.keycloak_admin.a_update_group(group_id=group_id, payload=payload)

        logger.debug(f"[_add_admin_role_internal] Successfully updated attributes for group {group_id}.")

    async def _remove_admin_role_internal(self, group_id: str, user_id: str) -> None:
        """
        내부 사용 목적: 사용자에게 admin 역할을 제거합니다. 권한 검사는 하지 않습니다.
        """
        # 그룹 조회
        group = await _get_group_safe(self.keycloak_admin, group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group with not found.",
            )

        attributes = group.get("attributes", {})
        owner_sub = attributes.get("owner", [None])[0]
        admins_list = attributes.get("admins", [])

        # 역할 확인
        if user_id == owner_sub:
            return
        if user_id not in admins_list:
            return

        # 관리자 제거
        admins_list.remove(user_id)
        attributes["admins"] = admins_list
        payload = {"attributes": attributes}
        await self.keycloak_admin.a_update_group(group_id=group_id, payload=payload)

        logger.debug(f"[_add_admin_role_internal] Successfully updated attributes for group {group_id}.")

    async def create_group(
        self,
        data: GroupRequest,
        user: get_current_user,
    ) -> GroupRepresentation:
        """
        새로운 Keycloak 그룹을 생성하고, 요청한 사용자를 'owner'로 지정합니다.
        """
        payload = data.model_dump(exclude_unset=True)
        parent_id = data.parentId
        if not parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Failed to create group: Creating groups need parentId.",
            )

        attributes = data.attributes or {}
        attributes["owner"] = [user.sub]
        if "admins" not in attributes:
            attributes["admins"] = []
        payload["attributes"] = attributes

        try:
            group_id = await self.keycloak_admin.a_create_group(payload=payload, parent=parent_id, skip_exists=False)
            if not group_id:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            await self.keycloak_admin.a_group_user_add(user_id=user.sub, group_id=group_id)
            created_group_info = await self.keycloak_admin.a_get_group(group_id=group_id)

            return GroupRepresentation(**created_group_info)

        except KeycloakPostError as e:
            if e.response_code == 409:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Group with name '{data.name}' or path '{data.path}' likely already exists.",
                )
            raise e
        except (KeycloakPutError, KeycloakGetError) as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Group created, but failed to add owner as member: {e}",
            )

    async def get_group(
        self,
        current_user: get_current_user,
        group_id: str = Path(),
    ) -> GroupRepresentation:
        """
        특정 그룹의 정보를 조회합니다. 그룹 멤버(owner, admin, member)만 접근 가능합니다.
        """
        group = await self._get_group_and_check_permission(
            group_id,
            current_user,
            allowed_roles=["owner", "admin", "member"],
        )

        return GroupRepresentation(**group)

    async def update_group(
        self,
        data: GroupUpdateRequest,
        current_user: get_current_user,
        group_id: str = Path(),
    ) -> GroupRepresentation:
        group = await self._get_group_and_check_permission(
            group_id,
            current_user,
            allowed_roles=["owner", "admin"],
        )

        payload = data.model_dump(exclude_unset=True)
        if not payload:
            current_group = await self.keycloak_admin.a_get_group(group_id=group_id)
            return GroupRepresentation(**current_group)

        if data.parentId and group.get("parentId") != data.parentId:
            await self._get_group_and_check_permission(
                data.parentId,
                current_user,
                allowed_roles=["owner", "admin", "member"],
            )

        try:
            await self.keycloak_admin.a_update_group(group_id=group_id, payload=payload)
            updated_group = await self.keycloak_admin.a_get_group(group_id=group_id)
            return GroupRepresentation(**updated_group)
        except (KeycloakPutError, KeycloakGetError):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update group",
            )

    async def delete_group(
        self,
        current_user: get_current_user,
        session: postgres_session,
        group_id: str = Path(),
    ) -> None:
        """
        그룹을 삭제합니다. 오직 'owner'만 가능합니다.
        그룹 삭제 시 관련된 모든 초대 정보도 DB에서 삭제됩니다.
        """
        await self._get_group_and_check_permission(
            group_id,
            current_user,
            allowed_roles=["owner"],
        )

        try:
            await self.keycloak_admin.a_delete_group(group_id=group_id)
            await self.invitation_repository.delete_by_group_id(session, group_id)
            logger.info(f"Group {group_id} deleted from Keycloak by user {current_user.sub}.")

        # 이미 없는 경우 성공
        except KeycloakDeleteError as e:
            if e.response_code != 404:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete group",
                )

    async def get_group_members_with_roles(
        self,
        user: get_current_user,
        group_id: str = Path(),
    ) -> List[Dict[str, Any]]:
        """
        그룹 멤버 목록과 각 멤버의 역할(owner, admin, member)을 반환합니다.
        그룹 멤버(owner, admin, member)만 접근 가능합니다.
        """
        # 그룹 조회
        group = await self._get_group_and_check_permission(
            group_id,
            user,
            allowed_roles=["owner", "admin", "member"],
        )

        # 역할 정보 추출
        members_raw = await self.keycloak_admin.a_get_group_members(group_id=group_id)
        attributes = group.get("attributes", {})
        owner_sub = attributes.get("owner", [None])[0]
        admin_subs = attributes.get("admins", [])

        # 멤버 목록에 역할 정보 추가
        members_with_roles = []
        for member in members_raw:
            member_sub = member.get("id")
            role = "member"
            if member_sub == owner_sub:
                role = "owner"
            elif member_sub in admin_subs:
                role = "admin"

            members_with_roles.append(
                {
                    "id": member_sub,
                    "username": member.get("username"),
                    "email": member.get("email"),
                    "firstName": member.get("firstName"),
                    "lastName": member.get("lastName"),
                    "role": role,
                }
            )
        return members_with_roles

    async def invite_member(
        self,
        data: GroupInvitationCreate,
        user: get_current_user,
        session: postgres_session,
        group_id: str = Path(),
    ) -> GroupInvitation:
        """
        이메일을 통해 사용자를 그룹에 초대합니다. owner 또는 admin만 가능합니다.
        """
        # 그룹 조회
        group = await self._get_group_and_check_permission(
            group_id,
            user,
            allowed_roles=["owner", "admin"],
        )

        group_name = group.get("name", group_id)
        invitee_email = data.invitee_email
        invitee_user = await _get_user_by_email_safe(self.keycloak_admin, str(invitee_email))

        if invitee_user:
            group_members = await self.keycloak_admin.a_get_group_members(
                group_id=group_id,
                query={"briefRepresentation": "true"},
            )
            if any(member["id"] == invitee_user["id"] for member in group_members):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with email '{invitee_email}' is already a member of group '{group_name}'.",
                )

        existing_invitation = await self.invitation_repository.get_instance(
            session=session,
            filters=[GroupInvitation.group_id == group_id, GroupInvitation.invitee_email == invitee_email],
        )
        if existing_invitation.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An active invitation for '{invitee_email}' to group '{group_name}' already exists.",
            )

        token = secrets.token_urlsafe(64)
        role_to_save = data.role if data.role == "admin" else "member"

        invitation = await self.invitation_repository.create(
            session=session,
            group_id=group_id,
            inviter_sub=user.sub,
            inviter_email=user.email,
            invitee_email=invitee_email,
            role=role_to_save,
            token=token,
        )

        # TODO: 이메일 발송 로직 필요

        return invitation

    async def accept_invitation(
        self,
        token: str,
        user: get_current_user,
        session: postgres_session,
    ):
        """
        제공된 토큰을 사용하여 그룹 초대를 수락합니다.
        """
        # 초대 정보를 가져옵니다
        invitation_instance = await self.invitation_repository.get_instance(
            session=session,  # 주입된 세션 사용
            filters=[GroupInvitation.token == token],
        )
        invitation = invitation_instance.scalar_one_or_none()

        # 초대장이 없는 경우
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired invitation token.",
            )

        # 초대 이메일이 일치하지 않는 경우
        if invitation.invitee_email != user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invitation email doesn't match.",
            )

        group_id = invitation.group_id
        role_to_assign = invitation.role or "member"

        # 유저가 존재하는 경우 넘어감
        try:
            await self.keycloak_admin.a_group_user_add(user_id=user.sub, group_id=group_id)
        except KeycloakPutError:
            pass

        # 관리자 권한 부여
        if role_to_assign == "admin":
            await self._add_admin_role_internal(group_id=group_id, user_id=user.sub)

        # 사용된 초대 정보 삭제
        try:
            await self.invitation_repository.delete(session=session, id=invitation.id)
        except Exception as e:
            logger.error(
                f"Failed to delete invitation (token: {token[:8]}...) from database after acceptance: {str(e)}",
                exc_info=True,
            )

    async def get_sent_invites(
        self,
        data: Annotated[GetInvitationsRequest, Query()],
        user: get_current_user,
        session: postgres_session,
    ):
        result = await self.invitation_repository.get_page(
            session,
            data.page,
            data.size,
            [self.invitation_repository.model.inviter_sub == user.sub],
            orderby=[desc(self.invitation_repository.model.created_at)],
        )

        return result.scalars().all()

    async def get_received_invites(
        self,
        data: Annotated[GetInvitationsRequest, Query()],
        user: get_current_user,
        session: postgres_session,
    ):
        result = await self.invitation_repository.get_page(
            session,
            data.page,
            data.size,
            [self.invitation_repository.model.invitee_email == user.email],
            orderby=[desc(self.invitation_repository.model.created_at)],
        )

        return result.scalars().all()

    async def delete_sent_invite(
        self,
        token: Annotated[str, Query()],
        user: get_current_user,
        session: postgres_session,
    ):
        result = await self.invitation_repository.get(
            session,
            [self.invitation_repository.model.inviter_sub == user.sub],
            [self.invitation_repository.model.token],
        )
        invite_token = result.scalar_one_or_none()

        if invite_token != token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await self.invitation_repository.delete_by_token(session, token)

    async def delete_receive_invite(
        self,
        token: Annotated[str, Query()],
        user: get_current_user,
        session: postgres_session,
    ):
        result = await self.invitation_repository.get(
            session,
            [self.invitation_repository.model.invitee_email == user.email],
            [self.invitation_repository.model.token],
        )
        invite_token = result.scalar_one_or_none()

        if invite_token != token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await self.invitation_repository.delete_by_token(session, token)

    async def add_admin_role(
        self,
        user: get_current_user,
        user_id: str = Path(),
        group_id: str = Path(),
    ) -> None:
        """
        사용자에게 admin 역할을 부여합니다. 그룹 owner만 가능합니다.
        """
        # 그룹 조회
        group = await self._get_group_and_check_permission(
            group_id,
            user,
            allowed_roles=["owner"],
        )

        # 오너 여부 조회
        owner_sub = group.get("attributes", {}).get("owner", [None])[0]
        if user_id == owner_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change the owner's role.",
            )

        # 멤버 여부 조회
        members = await self.keycloak_admin.a_get_group_members(
            group_id=group_id,
            query={"briefRepresentation": "true"},
        )
        if not any(member["id"] == user_id for member in members):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be a member of the group before being assigned as admin.",
            )

        # 관리자 권한 부여
        await self._add_admin_role_internal(group_id, user_id)

    async def remove_admin_role(
        self,
        user: get_current_user,
        user_id: str = Path(),
        group_id: str = Path(),
    ) -> None:
        """
        사용자의 admin 역할을 제거하고 member로 만듭니다. 그룹 owner만 가능합니다.
        """
        group = await self._get_group_and_check_permission(
            group_id,
            user,
            allowed_roles=["owner"],
        )

        owner_sub = group.get("attributes", {}).get("owner", [None])[0]
        if user_id == owner_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change the owner's role.",
            )

        await self._remove_admin_role_internal(group_id, user_id)

    async def remove_member(
        self,
        user: get_current_user,
        user_id: str = Path(),
        group_id: str = Path(),
    ) -> None:
        """
        그룹에서 멤버를 제거합니다. owner 또는 admin만 다른 사람을 제거 가능합니다.
        """
        # 그룹 조회
        group = await self._get_group_and_check_permission(
            group_id,
            user,
            allowed_roles=["owner", "admin", "member"],
        )

        # 멤버 여부 확인
        if group["current_user_role"] == "member" and user.sub != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove other from the group.",
            )

        # 오너 여부 확인
        attributes = group.get("attributes", {})
        owner_sub = attributes.get("owner", [None])[0]
        if user_id == owner_sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The group owner cannot be removed.",
            )

        # 관리자 여부 확인
        admin_subs = attributes.get("admins", [])
        if user_id in admin_subs:
            await self._remove_admin_role_internal(group_id, user_id)

        # 멤버 제거
        try:
            await self.keycloak_admin.a_group_user_remove(user_id=user_id, group_id=group_id)
        except KeycloakDeleteError as e:
            if e.response_code != 404:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to remove user from group",
                )
