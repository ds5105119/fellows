from sqlalchemy.ext.asyncio import AsyncSession

from src.app.user.model.user_data import UserBusinessData, UserData
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class UserDataCreateRepository(ABaseCreateRepository[UserData]):
    pass


class UserBusinessDataCreateRepository(ABaseCreateRepository[UserBusinessData]):
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


class UserBusinessDataReadRepository(ABaseReadRepository[UserBusinessData]):
    async def get_business_data(self, session: AsyncSession, sub: str):
        data = await self.get_instance(
            session,
            filters=[
                self.model.sub == sub,
            ],
        )
        return data.scalars().first()


class UserDataUpdateRepository(ABaseUpdateRepository[UserData]):
    pass


class UserBusinessDataUpdateRepository(ABaseUpdateRepository[UserBusinessData]):
    pass


class UserDataDeleteRepository(ABaseDeleteRepository[UserData]):
    pass


class UserBusinessDataDeleteRepository(ABaseDeleteRepository[UserBusinessData]):
    pass


class UserDataRepository(
    UserDataCreateRepository,
    UserDataReadRepository,
    UserDataUpdateRepository,
    UserDataDeleteRepository,
):
    pass


class UserBusinessDataRepository(
    UserBusinessDataCreateRepository,
    UserBusinessDataReadRepository,
    UserBusinessDataUpdateRepository,
    UserBusinessDataDeleteRepository,
):
    pass
