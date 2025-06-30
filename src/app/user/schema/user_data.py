from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from src.app.map.schema.map import Coord2AddrResponse
from src.app.user.model.user_data import AcademicStatus
from src.core.utils.pydantichelper import partial_model


class UserDataDto(BaseModel):
    overcome: int
    household_size: int

    multicultural: bool
    north_korean: bool
    single_parent_or_grandparent: bool
    homeless: bool
    new_resident: bool
    multi_child_family: bool
    extend_family: bool

    disable: bool
    veteran: bool
    disease: bool

    prospective_parents_or_infertility: bool
    pregnant: bool
    childbirth_or_adoption: bool

    farmers: bool
    fishermen: bool
    livestock_farmers: bool
    forestry_workers: bool

    unemployed: bool
    employed: bool

    academic_status: AcademicStatus

    model_config = ConfigDict(use_enum_values=True)


class UserBusinessDataDto(BaseModel):
    ja1101: bool = Field(default=False, description="예비창업자 (Pre-startup founder)")
    ja1102: bool = Field(default=False, description="영업중 (Currently operating)")
    ja1103: bool = Field(default=False, description="생계곤란/폐업예정자 (Economically distressed / Closing soon)")

    ja1201: bool = Field(default=False, description="음식적업 (Food business)")
    ja1202: bool = Field(default=False, description="제조업 (Manufacturing industry)")
    ja1299: bool = Field(default=False, description="기타업종 (Other industries)")

    ja2101: bool = Field(default=False, description="중소기업 (SME)")
    ja2102: bool = Field(default=False, description="사회복지시설 (Social welfare facility)")
    ja2103: bool = Field(default=False, description="기관/단체 (Organizations / Institutions)")

    ja2201: bool = Field(default=False, description="제조업 (Manufacturing)")
    ja2202: bool = Field(default=False, description="농업,임업 및 어업 (Agriculture, Forestry and Fisheries)")
    ja2203: bool = Field(default=False, description="정보통신업 (Information and Communication Technology)")
    ja2299: bool = Field(default=False, description="기타업종 (Other industries)")


@partial_model
class PartialUserDataDto(UserDataDto):
    pass


class LocationDto(BaseModel):
    location: list[float, float]

    @field_serializer("location")
    def serialize_location(self, location, _info):
        return [str(v) for v in location]


class OIDCAddressDto(LocationDto):
    locality: str
    sub_locality: str
    region: str
    postal_code: str
    country: str
    street: str
    formatted: str = Field(default="")


class KakaoAddressDto(LocationDto, Coord2AddrResponse):
    pass


class UserAttributes(OIDCAddressDto):
    username: str = Field(min_length=3, max_length=255, description="Username of the user")
    email: EmailStr = Field(max_length=255, description="Email address of the user")
    name: str
    birthdate: str
    gender: Literal["male", "female"]

    firstName: str | None = Field(default=None)
    lastName: str | None = Field(default=None)

    phoneNumber: str | None = Field(default=None)
    phoneNumberVerified: bool | None = Field(default=None)

    picture: str | None = Field(default=None)
    bio: str | None = Field(default=None, min_length=0, max_length=100)
    link: list[str] | None = Field(default=None, description="List of up to 4 personal links")
    userData: str | None = Field(default=None)


class UpdateUserAttributes(OIDCAddressDto):
    username: str | None = Field(default=None, min_length=3, max_length=255, description="Username of the user")
    email: EmailStr | None = Field(default=None, max_length=255, description="Email address of the user")
    name: str | None = Field(default=None)
    birthdate: str | None = Field(default=None)
    gender: Literal["male", "female"] | None = Field(default=None)

    firstName: str | None = Field(default=None)
    lastName: str | None = Field(default=None)

    phoneNumber: str | None = Field(default=None)
    phoneNumberVerified: bool | None = Field(default=None)

    picture: str | None = Field(default=None)
    bio: str | None = Field(default=None, min_length=0, max_length=100)
    link: list[str] | None = Field(default=None, description="List of up to 4 personal links")
    userData: str | None = Field(default=None)
