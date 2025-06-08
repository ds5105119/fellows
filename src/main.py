from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from webtool.auth import AnnoSessionBackend, KeycloakBackend
from webtool.throttle import LimitMiddleware

from src.app.router import router
from src.core.config import settings
from src.core.dependencies.auth import keycloak_openid
from src.core.dependencies.db import Redis
from src.core.lifespan import lifespan


class DebugHeaderMiddleware(BaseHTTPMiddleware):
    """요청‑응답 전체 헤더를 stdout 으로 덤프"""

    async def dispatch(self, request: Request, call_next):
        # ─── Request 헤더 ──────────────────────────────
        print("▼▼▼ REQUEST HEADERS ▼▼▼")
        for k, v in request.headers.items():
            print(f"{k}: {v}")
        print("▲▲▲ END REQUEST HEADERS ▲▲▲\n")

        response = await call_next(request)

        # ─── Response 헤더 ─────────────────────────────
        print("▼▼▼ RESPONSE HEADERS ▼▼▼")
        for k, v in response.headers.items():
            print(f"{k}: {v}")
        print("▲▲▲ END RESPONSE HEADERS ▲▲▲\n")

        return response


def create_application(debug=False) -> FastAPI:
    middleware = [
        Middleware(
            DebugHeaderMiddleware,  # type: ignore
        ),
        Middleware(
            CORSMiddleware,  # type: ignore
            allow_origins=settings.cors_allow_origin if not debug else ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(
            ProxyHeadersMiddleware,  # type: ignore
            trusted_hosts=settings.allowed_hosts if not debug else ["*"],
        ),
        Middleware(
            LimitMiddleware,  # type: ignore
            cache=Redis,
            auth_backend=KeycloakBackend(keycloak_openid),
            anno_backend=AnnoSessionBackend(session_name="th-session", secure=True, same_site="lax"),
        ),
    ]

    application = FastAPI(
        title=settings.project_name,
        docs_url=f"{settings.swagger_url}/docs",
        redoc_url=f"{settings.swagger_url}/redoc",
        openapi_url=f"{settings.swagger_url}/openapi.json",
        version="1.0.0",
        lifespan=lifespan,
        middleware=middleware,
        default_response_class=ORJSONResponse,
    )

    application.include_router(router, prefix=settings.api_url)

    return application


app = create_application(debug=settings.debug)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=settings.debug,
    )
