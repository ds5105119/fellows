from pydantic import BaseModel, EmailStr, Field, field_serializer

from src.app.map.schema.map import Coord2AddrResponse


class LocationDto(BaseModel):
    location: list[float, float] | None = Field(default=None)

    @field_serializer("location")
    def serialize_location(self, location, _info):
        return [str(v) for v in location]


class OIDCAddressDto(LocationDto):
    locality: str | None = Field(default=None)
    sub_locality: str | None = Field(default=None)
    region: str | None = Field(default=None)
    postal_code: str | None = Field(default=None)
    country: str | None = Field(default=None)
    street: str | None = Field(default=None)
    formatted: str | None = Field(default=None)


class KakaoAddressDto(LocationDto, Coord2AddrResponse):
    pass


class UserAttributes(BaseModel):
    sub: str
    bio: list[str] | None = Field(default=None)
    birthdate: list[str] | None = Field(default=None)
    country: list[str] | None = Field(default=None)
    formatted: list[str] | None = Field(default=None)
    gender: list[str] | None = Field(default=None)
    link: list[str] | None = Field(default=None)
    locale: list[str] | None = Field(default=None)
    locality: list[str] | None = Field(default=None)
    location: list[str] | None = Field(default=None)
    name: list[str] | None = Field(default=None)
    phoneNumber: list[str] | None = Field(default=None)
    phoneNumberVerified: list[str] | None = Field(default=None)
    picture: list[str] | None = Field(default=None)
    postal_code: list[str] | None = Field(default=None)
    region: list[str] | None = Field(default=None)
    street: list[str] | None = Field(default=None)
    sub_locality: list[str] | None = Field(default=None)
    userData: list[str] | None = Field(default=None)
    email: str | None = Field(default=None)


class ProjectAdminUserAttributes(BaseModel):
    sub: str
    bio: list[str] | None = Field(default=None)
    birthdate: list[str] | None = Field(default=None)
    country: list[str] | None = Field(default=None)
    formatted: list[str] | None = Field(default=None)
    gender: list[str] | None = Field(default=None)
    link: list[str] | None = Field(default=None)
    locale: list[str] | None = Field(default=None)
    locality: list[str] | None = Field(default=None)
    location: list[str] | None = Field(default=None)
    name: list[str] | None = Field(default=None)
    phoneNumber: list[str] | None = Field(default=None)
    picture: list[str] | None = Field(default=None)
    postal_code: list[str] | None = Field(default=None)
    region: list[str] | None = Field(default=None)
    street: list[str] | None = Field(default=None)
    sub_locality: list[str] | None = Field(default=None)
    email: str | None = Field(default=None)


class ExternalUserAttributes(BaseModel):
    sub: str
    bio: list[str] | None = Field(default=None)
    birthdate: list[str] | None = Field(default=None)
    gender: list[str] | None = Field(default=None)
    link: list[str] | None = Field(default=None)
    name: list[str] | None = Field(default=None)
    picture: list[str] | None = Field(default=None)
    email: str | None = Field(default=None)


class UpdateUserAttributes(BaseModel):
    bio: list[str] | None = Field(default=None)
    birthdate: list[str] | None = Field(default=None)
    country: list[str] | None = Field(default=None)
    formatted: list[str] | None = Field(default=None)
    gender: list[str] | None = Field(default=None)
    link: list[str] | None = Field(default=None)
    locale: list[str] | None = Field(default=None)
    locality: list[str] | None = Field(default=None)
    location: list[str] | None = Field(default=None)
    name: list[str] | None = Field(default=None)
    phoneNumber: list[str] | None = Field(default=None)
    phoneNumberVerified: list[str] | None = Field(default=None)
    picture: list[str] | None = Field(default=None)
    postal_code: list[str] | None = Field(default=None)
    region: list[str] | None = Field(default=None)
    street: list[str] | None = Field(default=None)
    sub_locality: list[str] | None = Field(default=None)
    userData: list[str] | None = Field(default=None)


class EmailUpdateRequest(BaseModel):
    email: EmailStr


class EmailUpdateVerify(BaseModel):
    email: EmailStr
    otp: str
