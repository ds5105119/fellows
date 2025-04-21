from typing import Annotated

from fastapi import HTTPException, Query, Request
from pydantic import ValidationError
from sqlalchemy import desc

from src.app.map.schema.map import Coord2AddrDto, Coord2AddrResponse
from src.core.config import settings
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session


class MapService:
    def __init__(self):
        pass

    async def coord_to_addr(
        self,
        request: Request,
        coord: Annotated[Coord2AddrDto, Query()],
    ) -> Coord2AddrResponse:
        client = request.app.requests_client
        headers = {"Authorization": f"KakaoAK {settings.kakao_api.key}"}
        payload = coord.model_dump()

        response = await client.get(
            "https://dapi.kakao.com/v2/local/geo/coord2address.json",
            headers=headers,
            params=payload,
        )
        data = response.json()

        try:
            return Coord2AddrResponse.model_validate(data)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail="Invalid coordinate")
