from typing import Annotated

from fastapi import APIRouter, Depends
from webtool.throttle import limiter

from src.app.map.api.dependencies import map_service
from src.app.map.schema.map import Coord2AddrResponse

router = APIRouter()


@limiter(max_requests=300)
@router.get("/coord2addr")
async def coord_to_addr(
    result: Annotated[Coord2AddrResponse, Depends(map_service.coord_to_addr)],
) -> Coord2AddrResponse:
    return result
