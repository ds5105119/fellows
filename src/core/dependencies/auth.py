from datetime import date
from typing import Annotated, Any, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from keycloak import KeycloakAdmin, KeycloakOpenID, KeycloakOpenIDConnection
from pydantic import BaseModel, Field, field_validator

from src.core.config import settings


class Address(BaseModel):
    formatted: str | None = Field(default=None)
    street_address: str | None = Field(default=None)
    locality: str | None = Field(default=None)
    region: str | None = Field(default=None)
    postal_code: str | None = Field(default=None)
    country: str | None = Field(default=None)


class User(BaseModel):
    sub: str
    email: str
    username: str
    gender: str
    birthdate: str | date
    access_token: str
    location: list[int] | None = Field(default_factory=list)

    # 확장 필드들
    name: str | None = Field(default=None)
    given_name: str | None = Field(default=None)
    family_name: str | None = Field(default=None)
    email_verified: bool | None = Field(default=None)
    address: Address | None = Field(default=None)
    groups: list[str] | None = Field(default_factory=list)
    realm_access: dict[str, list[str]] | None = Field(default_factory=dict)
    resource_access: dict[str, Any] | None = Field(default_factory=dict)
    scope: str | None = Field(default=None)
    sub_locality: str | None = Field(default=None)

    @field_validator("birthdate", mode="before")
    def parse_birthdate(cls, value):
        return date.fromisoformat(value) if isinstance(value, str) else value


class ExtendHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        auth = request.scope.get("auth")
        return auth


http_bearer = ExtendHTTPBearer()


async def _get_current_user(
    data: Annotated[dict, Depends(http_bearer, use_cache=False)],
) -> User:
    print(data)
    if not data:
        raise HTTPException(status_code=403)

    return User(**data)


async def _get_current_user_without_error(
    data: Annotated[dict, Depends(http_bearer, use_cache=False)],
) -> User | None:
    return User(**data) if data else None


get_current_user = Annotated[User, Depends(_get_current_user)]
get_current_user_without_error = Annotated[User | None, Depends(_get_current_user_without_error)]

keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak.server_url,
    client_id=settings.keycloak.client_id,
    realm_name=settings.keycloak.realm_name,
    client_secret_key=settings.keycloak.client_secret_key,
)
keycloak_openid_connection = KeycloakOpenIDConnection(
    server_url=settings.keycloak_admin.server_url,
    username=settings.keycloak_admin.username,
    password=settings.keycloak_admin.password,
    realm_name=settings.keycloak_admin.realm_name,
    user_realm_name=settings.keycloak_admin.user_realm_name,
    client_id=settings.keycloak_admin.client_id,
    client_secret_key=settings.keycloak_admin.client_secret_key,
    verify=settings.keycloak_admin.verify,
)
keycloak_admin = KeycloakAdmin(connection=keycloak_openid_connection)
