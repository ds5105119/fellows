from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.app.user.api.dependencies import group_service
from src.app.user.schema.group import *

router = APIRouter()


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_new_group(
    created_group: Annotated[GroupResponse, Depends(group_service.create_group)],
):
    """새로운 그룹을 생성합니다. `parentId`는 필수입니다."""
    return created_group


@router.get("/{group}", response_model=GroupResponse)
async def read_group(
    group: Annotated[GroupResponse, Depends(group_service.get_group_by_id)],
):
    return group


@router.get("/", response_model=GroupsPaginatedResponse)
async def read_groups(
    groups: Annotated[GroupsPaginatedResponse, Depends(group_service.get_groups)],
):
    return groups


@router.put("/{group}", response_model=GroupResponse)
async def update_group(
    group: Annotated[GroupResponse, Depends(group_service.update_group)],
):
    return group


@router.delete("/{group}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group(
    _: Annotated[None, Depends(group_service.delete_group)],
):
    return None


# --- Group Member & Role Management Endpoints ---


@router.post("/{group}/invitations", response_model=GroupInvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_user_to_group(
    invitation: Annotated[GroupInvitationResponse, Depends(group_service.invite_member_to_group)],
):
    """그룹에 사용자를 이메일로 초대합니다. (owner 또는 admin 접근 가능)"""
    return invitation


@router.get("/invitations/accept", response_model=GroupResponse)
async def accept_group_invitation(
    result: Annotated[GroupResponse, Depends(group_service.accept_group_invitation)],
):
    return result


@router.put("/{group}/member/{member}", response_model=GroupResponse)
async def update_group_member_details(
    result: Annotated[GroupResponse, Depends(group_service.update_group_member_details)],
):
    return result


@router.delete("/{group}/member/{member}", status_code=status.HTTP_204_NO_CONTENT)
async def update_group_member_details(
    _: Annotated[None, Depends(group_service.remove_member_from_group)],
):
    pass


# --- Group Invitation Endpoints ---


@router.get("/invitations/sent", response_model=GroupInvitationsPaginatedResponse)
async def get_sent_invitations(
    invitations: Annotated[GroupInvitationsPaginatedResponse, Depends(group_service.get_sent_invites)],
):
    """자신이 보낸 초대 목록을 조회합니다."""
    return invitations


@router.delete("/invitations/sent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sent_invitation(
    _: Annotated[None, Depends(group_service.delete_sent_invite)],
):
    """자신이 보낸 초대를 삭제합니다."""
    return None


@router.get("/invitations/received", response_model=GroupInvitationsPaginatedResponse)
async def get_received_invitations(
    invitations: Annotated[GroupInvitationsPaginatedResponse, Depends(group_service.get_received_invites)],
):
    """자신이 받은 초대 목록을 조회합니다."""
    return invitations


@router.delete("/invitations/received", status_code=status.HTTP_204_NO_CONTENT)
async def delete_received_invitation(
    _: Annotated[None, Depends(group_service.delete_receive_invite)],
):
    """자신이 받은 초대를 삭제합니다."""
    return None
