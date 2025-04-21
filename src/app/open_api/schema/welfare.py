from pydantic import BaseModel, Field


class WelfareDto(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(10, ge=1, le=20, description="Page size")
    tag: str = Field(default="")
    order_by: str = Field(default="views")
