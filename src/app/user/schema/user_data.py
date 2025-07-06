from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer

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


class ExternalUserAttributes(BaseModel):
    bio: list[str] | None = Field(default=None)
    birthdate: list[str] | None = Field(default=None)
    country: list[str] | None = Field(default=None)
    gender: list[str] | None = Field(default=None)
    link: list[str] | None = Field(default=None)
    name: list[str] | None = Field(default=None)
    picture: list[str] | None = Field(default=None)


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
