from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class GroupRequest(BaseModel):
    name: str | None = Field(default=None)
    path: str | None = Field(default=None)
    parentId: str | None = Field(default=None)
    subGroupCount: int | None = Field(default=None)
    subGroups: list["GroupRequest"] | None = Field(default=None)
    attributes: dict[str, list[str]] | None = Field(default=None)


class GroupUpdateRequest(BaseModel):
    parentId: str | None = Field(default=None)
    name: str | None = Field(default=None)


class GroupRepresentation(BaseModel):
    id: str | None = Field(default=None)
    name: str | None = Field(default=None)
    path: str | None = Field(default=None)
    parentId: str | None = Field(default=None)
    subGroupCount: int | None = Field(default=None)
    subGroups: list["GroupRepresentation"] | None = Field(default=None)
    attributes: dict[str, list[str]] | None = Field(default=None)
    realmRoles: list[str] | None = Field(default=None)
    clientRoles: dict[str, list[str]] | None = Field(default=None)
    access: dict[str, bool] | None = Field(default=None)


class GroupInvitationCreate(BaseModel):
    invitee_email: EmailStr
    role: str | None = Field(default=None)


class GroupInvitationResponse(BaseModel):
    id: int
    group_id: str
    inviter_sub: str
    inviter_email: EmailStr
    invitee_email: EmailStr
    role: str | None = Field(default=None)
    token: str
    created_at: datetime

    class Config:
        from_attributes = True


class GetInvitationRequest(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(10, ge=1, le=20, description="Page size")
