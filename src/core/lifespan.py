import logging
import logging.config
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
from src.core.dependencies.db import Postgres, Redis
from src.core.dependencies.infra import nc

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # app start
    logging.config.dictConfig(LOGGING_CONFIG)
    log = logging.getLogger(__name__)

    log.info("Application Started")
    await nc.connect(servers=settings.nats.server, name=settings.nats.name)
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
    log.info("Application Stopped")
