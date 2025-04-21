from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from src.app.open_api.api.dependencies import (
    fiscal_data_manager,
    gov24_service_conditions_manager,
    gov24_service_detail_manager,
    gov24_service_list_manager,
)
from src.core.config import settings
from src.core.dependencies.db import Postgres, Redis, create_postgis_extension
from src.core.dependencies.infra import nc


@asynccontextmanager
async def lifespan(app: FastAPI):
    # app start
    print("Application Started")
    await nc.connect(servers=settings.nats.server, name=settings.nats.name)
    await create_postgis_extension()
    await fiscal_data_manager.init()
    await gov24_service_conditions_manager.init()
    await gov24_service_detail_manager.init()
    await gov24_service_list_manager.init()
    app.requests_client = httpx.AsyncClient()

    yield

    # app shutdown
    await Postgres.aclose()
    await Redis.aclose()
    await app.requests_client.aclose()
    print("Application Stopped")
