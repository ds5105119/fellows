from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from webtool.cache import RedisCache
from webtool.db import AsyncDB, SyncDB

from src.core.config import settings

Postgres = AsyncDB(settings.postgres_dsn.unicode_string())
Postgres_sync = SyncDB(settings.sync_postgres_dsn.unicode_string())
Wakapi_Postgres = AsyncDB(settings.wakapi_postgres_dsn.unicode_string())
Redis = RedisCache(settings.redis_dsn.unicode_string())

postgres_session = Annotated[AsyncSession, Depends(Postgres)]
wakapi_postgres_session = Annotated[AsyncSession, Depends(Wakapi_Postgres)]


async def create_postgis_extension(async_db: AsyncDB = Postgres):
    async with async_db.session_factory() as session:
        try:
            result = await session.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'postgis';"))
            if result.scalar() is not None:
                print("✅PostGIS extension is already installed!")
            else:
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                await session.commit()
                print("✅PostGIS extension installed successfully!")

        except Exception as e:
            print(f"❌Error installing PostGIS extension: {e}")
            await session.rollback()
