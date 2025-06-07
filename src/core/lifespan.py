import logging
import logging.config
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from src.core.dependencies.db import Postgres, Redis

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
    logging.config.dictConfig(LOGGING_CONFIG)
    log = logging.getLogger(__name__)
    log.info("Application Started")

    # await nc.connect(servers=settings.nats.server, name=settings.nats.name)
    app.requests_client = httpx.AsyncClient()

    yield

    await Postgres.aclose()
    await Redis.aclose()
    await app.requests_client.aclose()
    log.info("Application Stopped")
