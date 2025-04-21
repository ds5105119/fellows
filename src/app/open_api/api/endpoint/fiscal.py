from typing import Annotated, Any

from fastapi import APIRouter, Depends
from webtool.throttle import limiter

from src.app.open_api.api.dependencies import fiscal_service

router = APIRouter()


@limiter(max_requests=300)
@router.get("/detail")
async def get_detail_fiscal(result: Annotated[Any, Depends(fiscal_service.get_fiscal)]):
    return result


@limiter(max_requests=300)
@router.get("/year")
async def get_year_fiscal(result: Annotated[Any, Depends(fiscal_service.get_fiscal_by_year)]):
    return result


@limiter(max_requests=300)
@router.get("/year-offc")
async def get_year_offc_fiscal(result: Annotated[Any, Depends(fiscal_service.get_fiscal_by_year_offc)]):
    return result
