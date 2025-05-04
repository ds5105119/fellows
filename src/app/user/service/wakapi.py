from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.user.repository.wakapi import WakapiUserRepository
from src.core.dependencies.auth import User, get_current_user
from src.core.dependencies.db import wakapi_postgres_session


class WakapiService:
    def __init__(
        self,
        repository: WakapiUserRepository,
    ):
        self.repository = repository

    async def make_wakapi_user(self, session: AsyncSession, user: User) -> str:
        key = str(uuid4())
        aware_dt = datetime.now(UTC)
        naive_dt = aware_dt.replace(tzinfo=None)  # ← tz 제거

        try:
            await self.repository.create(
                session,
                id=user.sub,
                api_key=key,
                created_at=naive_dt,
                last_logged_in_at=naive_dt,
                share_data_max_days=-1,
                share_editors=True,
                share_languages=True,
                share_projects=True,
                share_oss=True,
                share_machines=True,
                share_labels=True,
                share_activity_chart=True,
            )

        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Unknown error")

        return key

    async def read_api_key(
        self,
        session: wakapi_postgres_session,
        user: get_current_user,
    ) -> str:
        key = await self.repository.get_user_key_by_sub(session, user.sub)

        if not key:
            key = await self.make_wakapi_user(session, user)

        return key
