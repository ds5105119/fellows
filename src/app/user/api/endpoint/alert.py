from typing import Annotated

from fastapi import APIRouter, Depends, Path

from src.app.user.api.dependencies import alert_service
from src.app.user.schema.alert import *
from src.app.user.service.alert import AlertService
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session

router = APIRouter()


@router.get("", response_model=AlertPaginatedResponse)
async def get_alerts(
    alerts: Annotated[AlertPaginatedResponse, Depends(alert_service.get_alerts)],
):
    return alerts


@router.patch("/{alert_id}/read", response_model=AlertDto)
async def mark_alert_as_read(alert: Annotated[AlertDto, Depends(alert_service.mark_alert_as_read)]):
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    _: Annotated[AlertDto, Depends(alert_service.delete_alert)],
):
    pass
