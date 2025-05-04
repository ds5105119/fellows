from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.app.user.api.dependencies import wakapi_service

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
async def read_api_key(api_key: Annotated[str, Depends(wakapi_service.read_api_key)]) -> str:
    return api_key
