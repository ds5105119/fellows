from pydantic import BaseModel, Field


class FiscalByYearDto(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(50, ge=1, le=100, description="Page size")
    start_year: str | None = Field(default=None)
    end_year: str | None = Field(default=None)
    order_by: str = Field(default="FSCL_YY")


class FiscalByYearOffcDto(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(50, ge=1, le=100, description="Page size")
    start_year: str | None = Field(default=None)
    end_year: str | None = Field(default=None)
    offc_name: str | None = Field(default=None)
    dept_code: int | None = Field(default=None)
    order_by: str = Field(default="OFFC_NM")


class FiscalDto(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(50, ge=1, le=100, description="Page size")
    start_year: str | None = Field(default=None)
    end_year: str | None = Field(default=None)
    offc_name: str | None = Field(default=None)
    dept_code: int | None = Field(default=None)
    order_by: str = Field(default="OFFC_NM")
