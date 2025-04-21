from sqlalchemy.ext.asyncio import AsyncSession

from src.app.user.model.user_data import UserData
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class UserDataCreateRepository(ABaseCreateRepository[UserData]):
    pass


class UserDataReadRepository(ABaseReadRepository[UserData]):
    async def get_user_data(self, session: AsyncSession, sub: str):
        data = await self.get_instance(
            session,
            filters=[
                self.model.sub == sub,
            ],
        )
        return data.scalars().first()


class UserDataUpdateRepository(ABaseUpdateRepository[UserData]):
    pass


class UserDataDeleteRepository(ABaseDeleteRepository[UserData]):
    pass


class UserDataRepository(
    UserDataCreateRepository,
    UserDataReadRepository,
    UserDataUpdateRepository,
    UserDataDeleteRepository,
):
    pass
