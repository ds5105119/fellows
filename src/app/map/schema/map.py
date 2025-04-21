from typing import Literal

from pydantic import BaseModel, Field


class Address(BaseModel):
    address_name: str
    region_1depth_name: str
    region_2depth_name: str
    region_3depth_name: str
    mountain_yn: Literal["Y", "N"]
    main_address_no: str
    sub_address_no: str
    zip_code: str | None = Field(default=None)


class RoadAddress(BaseModel):
    address_name: str
    region_1depth_name: str
    region_2depth_name: str
    region_3depth_name: str
    road_name: str
    underground_yn: Literal["Y", "N"]
    main_building_no: str
    sub_building_no: str
    building_name: str
    zone_no: str


class Coord2AddrDto(BaseModel):
    x: str
    y: str
    input_coord: Literal["WGS84", "WCONGNAMUL", "CONGNAMUL", "WTM", "TM"] = Field(default="WGS84")


class Coord2AddrResponseMeta(BaseModel):
    total_count: int = Field(ge=0, le=1)


class Coord2AddrResponseDocument(BaseModel):
    address: Address
    road_address: RoadAddress


class Coord2AddrResponse(BaseModel):
    meta: Coord2AddrResponseMeta
    documents: list[Coord2AddrResponseDocument]
