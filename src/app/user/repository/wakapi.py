from sqlalchemy.ext.asyncio import AsyncSession

from src.app.user.model.wakapi import Users
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class WakapiUserCreateRepository(ABaseCreateRepository[Users]):
    pass


class WakapiUserReadRepository(ABaseReadRepository[Users]):
    async def get_user_by_sub(self, session: AsyncSession, sub: str):
        data = await self.get(
            session,
            filters=[
                self.model.id == sub,
            ],
        )
        return data.first()

    async def get_user_key_by_sub(self, session: AsyncSession, sub: str):
        data = await self.get(
            session,
            filters=[
                self.model.id == sub,
            ],
            columns=[self.model.api_key],
        )

        data = data.first()

        if data:
            return data[0]
        return data


class WakapiUserUpdateRepository(ABaseUpdateRepository[Users]):
    pass


class WakapiUserDeleteRepository(ABaseDeleteRepository[Users]):
    pass


class WakapiUserRepository(
    WakapiUserCreateRepository,
    WakapiUserReadRepository,
    WakapiUserUpdateRepository,
    WakapiUserDeleteRepository,
):
    pass
