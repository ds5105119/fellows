from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AlertDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sub: str
    message: str
    is_read: bool
    created_at: datetime
    link: str


class UpdateAlertDto(BaseModel):
    is_read: Optional[bool] = None


class AlertListQueryDto(BaseModel):
    page: int
    size: int


class AlertPaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[AlertDto]
    total: int
