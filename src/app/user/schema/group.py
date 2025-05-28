from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Membership Schemas (새로운 모델) ---
class MembershipBase(BaseModel):
    pass


class MembershipResponse(MembershipBase):
    model_config = ConfigDict(from_attributes=True)
    sub: str


# --- GroupPosition Schemas ---
class GroupPositionBase(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)


class GroupPositionCreateRequest(GroupPositionBase):
    pass


class GroupPositionUpdateRequest(BaseModel):  # 부분 업데이트
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None)


class GroupPositionResponse(GroupPositionBase):
    model_config = ConfigDict(from_attributes=True)

    group_id: str
    name: str


# --- GroupMembershipPositionLink Schemas (새로운 모델) ---
class GroupMembershipPositionLinkBase(BaseModel):
    position_id: int | None = Field(default=None)
    role: int = Field(default=2)


class GroupMembershipPositionLinkCreateRequest(GroupMembershipPositionLinkBase):
    membership_sub: str
    pass


class GroupMembershipPositionLinkUpdateRequest(BaseModel):
    position_id: int | None = Field(default=None)
    role: int | None = None


class KeycloakUserRepresentation(BaseModel):
    username: str
    email: str
    firstName: str | None = Field(default=None)
    lastName: str | None = Field(default=None)
    attributes: dict[str, list[Any]] = Field(default_factory=dict)


class GroupMembershipPositionLinkResponse(GroupMembershipPositionLinkBase):
    model_config = ConfigDict(from_attributes=True)
    group_id: str
    membership_sub: str
    joined_at: datetime
    position: GroupPositionResponse | None = Field(default=None)
    userdata: KeycloakUserRepresentation | None = Field(default=None)


# --- Group Schemas ---
class GroupBase(BaseModel):
    name: str = Field(max_length=255)
    description: str | None = None
    group_type: str | None = Field(default=None, max_length=50)
    parent_id: str | None = None

    # RBAC 설정 필드 (숫자 값)
    role_view_groups: int = Field(default=3)
    role_edit_groups: int = Field(default=1)
    role_create_sub_groups: int = Field(default=2)
    role_invite_groups: int = Field(default=1)


class GroupCreateRequest(GroupBase):
    pass


class GroupUpdateRequest(BaseModel):  # 그룹의 일부 정보만 업데이트
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    group_type: str | None = Field(default=None, max_length=50)
    parent_id: str | None = Field(default=None)
    role_view_groups: int | None = Field(default=None)
    role_edit_groups: int | None = Field(default=None)
    role_create_sub_groups: int | None = Field(default=None)
    role_invite_groups: int | None = Field(default=None)


class GroupOnlyResponse(GroupBase):  # 계층 구조에서 사용될 간단한 그룹 정보
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by_sub: str | None = Field(default=None)
    created_at: datetime
    updated_at: datetime
    memberships: list[GroupMembershipPositionLinkResponse] = Field(default_factory=list)


class GroupResponse(GroupBase):  # 단일 그룹 상세 조회 시 응답
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_by_sub: str | None = Field(default=None)
    created_at: datetime
    updated_at: datetime
    memberships: list[GroupMembershipPositionLinkResponse] = Field(default_factory=list)

    parent: GroupOnlyResponse | None = Field(default=None)
    children: list[GroupOnlyResponse] = Field(default_factory=list)


class GroupsPaginatedResponse(BaseModel):  # 여러 그룹 목록 조회 시 응답
    model_config = ConfigDict(from_attributes=True)
    total: int
    items: list[GroupOnlyResponse]  # 상세 멤버십 정보는 제외


# --- GroupInvitation Schemas ---
class GroupInvitationCreateRequest(BaseModel):
    # group_id는 경로 파라미터로 받을 것
    invitee_email: EmailStr
    role: int = Field(
        default=2, description="Role (numeric) to assign upon invitation acceptance"
    )  # 기본값 member 역할 숫자


class GroupInvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: str
    inviter_sub: str
    inviter_email: EmailStr  # 모델에 있으므로 Optional 아님
    invitee_email: EmailStr
    role: int | None = Field(default=None)  # 모델에 role이 int|None이므로 Optional[int]
    token: str  # 응답에는 포함하되, 클라이언트가 저장/노출하지 않도록 주의
    created_at: datetime


class GroupInvitationsPaginatedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[GroupInvitationResponse]


class GetInvitationsRequest(BaseModel):  # 페이징 요청 스키마
    page: int = Field(0, ge=0, description="Page number starting from 0")
    size: int = Field(10, ge=1, le=100, description="Number of items per page")


# --- GroupSchedule Schemas (새로운 모델) ---
class GroupScheduleBase(BaseModel):
    date: datetime  # 날짜 및 시간 정보
    work_type: str | None = Field(default=None, max_length=50)
    hours_planned: float = Field(default=0.0, ge=0)
    hours_actual: float = Field(default=0.0, ge=0)
    note: str | None = None


class GroupScheduleCreateRequest(GroupScheduleBase):
    # group_id와 membership_sub는 경로 또는 컨텍스트로 주어짐
    membership_sub: str  # 어떤 멤버의 스케줄인지 명시
    pass


class GroupScheduleUpdateRequest(BaseModel):  # 부분 업데이트
    date: datetime | None = Field(default=None)
    work_type: str | None = Field(default=None, max_length=50)
    hours_planned: float | None = Field(default=None, ge=0)
    hours_actual: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None)


class GroupScheduleResponse(GroupScheduleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: str
    membership_sub: str
    created_at: datetime
    updated_at: datetime
