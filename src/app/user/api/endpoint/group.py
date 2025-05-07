from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from src.app.user.api.dependencies import group_service
from src.app.user.model.group import GroupInvitation
from src.app.user.schema.group import GroupInvitationResponse, GroupRepresentation

router = APIRouter()


@router.post("/", response_model=GroupRepresentation, status_code=status.HTTP_201_CREATED)
async def create_new_group(
    created_group: Annotated[GroupRepresentation, Depends(group_service.create_group)],
):
    """새로운 그룹을 생성합니다. `parentId`는 필수입니다."""
    return created_group


@router.get("/{group_id}", response_model=GroupRepresentation)
async def read_group(
    group_info: Annotated[GroupRepresentation, Depends(group_service.get_group)],
):
    """특정 그룹 정보를 조회합니다. (멤버 이상 접근 가능)"""
    return group_info


@router.put("/{group_id}", response_model=GroupRepresentation)
async def update_group(
    updated_group: Annotated[GroupRepresentation, Depends(group_service.update_group)],
):
    """그룹 기본 정보(이름, parentId)를 수정합니다. (owner 또는 admin 접근 가능)"""
    return updated_group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group(
    _: Annotated[None, Depends(group_service.delete_group)],
):
    """그룹을 삭제합니다. (Owner만 가능)"""
    return None


# --- Group Member & Role Management Endpoints ---


@router.get("/{group_id}/members", response_model=list[dict[str, Any]])
async def read_group_members(
    members: Annotated[list[dict[str, Any]], Depends(group_service.get_group_members_with_roles)],
):
    """그룹 멤버 목록과 역할을 조회합니다. (멤버 이상 접근 가능)"""
    return members


@router.put("/{group_id}/admins/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_group_admin_role(
    _: Annotated[None, Depends(group_service.add_admin_role)],
):
    """멤버에게 Admin 역할을 부여합니다. (Owner만 가능)"""
    return None


@router.delete("/{group_id}/admins/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_admin_role(
    _: Annotated[None, Depends(group_service.remove_admin_role)],
):
    """Admin 역할을 제거하고 Member로 만듭니다. (Owner만 가능)"""
    return None


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    _: Annotated[None, Depends(group_service.remove_member)],
):
    """그룹에서 멤버를 제거합니다. (owner/admin은 타인 제거 가능, member는 자신만 제거 가능)"""
    return None


# --- Group Invitation Endpoints ---


@router.post("/{group_id}/invitations", response_model=GroupInvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_user_to_group(
    invitation_db: Annotated[GroupInvitation, Depends(group_service.invite_member)],
):
    """그룹에 사용자를 이메일로 초대합니다. (owner 또는 admin 접근 가능)"""
    return GroupInvitationResponse.model_validate(invitation_db)


@router.post("/invitations/accept", status_code=status.HTTP_200_OK)
async def accept_group_invitation(
    result: Annotated[dict[str, Any], Depends(group_service.accept_invitation)],
):
    """그룹 초대를 수락합니다."""
    return result


@router.get("/invitations/sent", response_model=list[GroupInvitationResponse])
async def get_sent_invitations(
    invitations_raw: Annotated[list[dict[str, Any]], Depends(group_service.get_sent_invites)],
):
    """자신이 보낸 초대 목록을 조회합니다."""
    return [GroupInvitationResponse.model_validate(inv) for inv in invitations_raw]


@router.get("/invitations/received", response_model=list[GroupInvitationResponse])
async def get_received_invitations(
    invitations_raw: Annotated[list[dict[str, Any]], Depends(group_service.get_received_invites)],
):
    """자신이 받은 초대 목록을 조회합니다."""
    return [GroupInvitationResponse.model_validate(inv) for inv in invitations_raw]


@router.delete("/invitations/sent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sent_invitation(
    _: Annotated[None, Depends(group_service.delete_sent_invite)],
):
    """자신이 보낸 초대를 삭제합니다."""
    return None


@router.delete("/invitations/received", status_code=status.HTTP_204_NO_CONTENT)
async def delete_received_invitation(
    _: Annotated[None, Depends(group_service.delete_receive_invite)],
):
    """자신이 받은 초대를 삭제합니다."""
    return None
