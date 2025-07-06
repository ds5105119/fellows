from sqlalchemy.ext.asyncio import AsyncSession

from src.app.user.model.alert import Alert
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class AlertCreateRepository(ABaseCreateRepository[Alert]):
    pass


class AlertReadRepository(ABaseReadRepository[Alert]):
    pass


class AlertUpdateRepository(ABaseUpdateRepository[Alert]):
    pass


class AlertDeleteRepository(ABaseDeleteRepository[Alert]):
    pass


class AlertRepository(
    AlertCreateRepository,
    AlertReadRepository,
    AlertUpdateRepository,
    AlertDeleteRepository,
):
    pass
