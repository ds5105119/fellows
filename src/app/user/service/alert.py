from typing import Annotated

from fastapi import HTTPException, Path, Query, status

from src.app.user.repository.alert import AlertRepository
from src.app.user.schema.alert import *
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session


class AlertService:
    def __init__(self, alert_repo: AlertRepository):
        self.alert_repo = alert_repo

    async def get_alerts(
        self,
        user: get_current_user,
        data: Annotated[AlertListQueryDto, Query()],
        session: postgres_session,
    ):
        filters = [self.alert_repo.model.sub == user.sub]

        result = await self.alert_repo.get_page_with_total(
            session,
            page=data.page,
            size=data.size,
            filters=filters,
            orderby=[self.alert_repo.model.created_at.desc()],
        )

        return AlertPaginatedResponse.model_validate(result, from_attributes=True)

    async def mark_alert_as_read(
        self,
        user: get_current_user,
        session: postgres_session,
        alert_id: Annotated[list[int], Query()],
    ):
        alerts = await self.alert_repo.get(session, filters=[self.alert_repo.model.id in alert_id])
        alerts = alerts.scalars().all()

        await self.alert_repo.update(
            session,
            filters=[self.alert_repo.model.id in [alert.id for alert in alerts]],
            is_read=True,
        )
        return AlertDto.model_validate(alerts, from_attributes=True)

    async def delete_alert(
        self,
        user: get_current_user,
        session: postgres_session,
        alert_id: int = Path(),
    ):
        alert = await self.alert_repo.get(session, filters=[self.alert_repo.model.id == alert_id])
        alert = alert.scalars().one_or_none()

        if not alert or alert.sub != user.sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        await self.alert_repo.delete(session, alert_id)
        return {"message": "Alert deleted successfully"}
