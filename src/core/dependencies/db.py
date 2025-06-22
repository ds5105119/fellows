from typing import Annotated
from uuid import uuid4

import boto3
from fastapi import Depends
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import AsyncSession
from webtool.cache import RedisCache, RedisConfig
from webtool.db import AsyncDB

from src.core.config import settings

## Webtool에서 session_args와 engine_args 반대로 적용함. 차후 수정 예정
Postgres = AsyncDB(
    settings.postgres_dsn.unicode_string(),
    session_args={
        "poolclass": NullPool,
        "future": True,
        "connect_args": {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        },
    },
)
Wakapi_Postgres = AsyncDB(
    settings.wakapi_postgres_dsn.unicode_string(),
    session_args={
        "poolclass": NullPool,
        "future": True,
        "connect_args": {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        },
    },
)

postgres_session = Annotated[AsyncSession, Depends(Postgres)]
wakapi_postgres_session = Annotated[AsyncSession, Depends(Wakapi_Postgres)]


Redis = RedisCache(
    settings.redis_dsn.unicode_string(),
    config=RedisConfig(
        username=settings.redis.user,
        password=settings.redis.password,
    ),
)


r2 = boto3.client(
    service_name="s3",
    endpoint_url=f"https://{settings.cloudflare.account_id}.r2.cloudflarestorage.com",
    aws_access_key_id=settings.cloudflare.access_key_id,
    aws_secret_access_key=settings.cloudflare.secret_access_key,
    region_name="auto",
)


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
