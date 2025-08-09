from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from webtool.cache import RedisCache, RedisConfig
from webtool.db import AsyncDB

from src.core.config import settings

DB = AsyncDB(settings.postgres_dsn.unicode_string())
Wakapi_Postgres = AsyncDB(settings.wakapi_postgres_dsn.unicode_string())

db_session = Annotated[AsyncSession, Depends(DB)]
wakapi_postgres_session = Annotated[AsyncSession, Depends(Wakapi_Postgres)]


Redis = RedisCache(
    settings.redis_dsn.unicode_string(),
    config=RedisConfig(
        username=settings.redis.user,
        password=settings.redis.password,
    ),
)


async def create_postgis_extension(async_db: AsyncDB = DB):
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
