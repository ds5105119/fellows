from typing import Annotated, Any

from fastapi import APIRouter, Depends
from webtool.throttle import limiter

from src.app.gov_api.api.dependencies import gov_welfare_service

router = APIRouter()


@limiter(max_requests=300)
@router.get("/recommend")
async def recommend_welfare(result: Annotated[Any, Depends(gov_welfare_service.get_personal_welfare)]):
    return result


@limiter(max_requests=300)
@router.get("/business")
async def business_welfare(result: Annotated[Any, Depends(gov_welfare_service.get_business_welfare)]):
    return result


@limiter(max_requests=300)
@router.get("/")
async def get_welfare(result: Annotated[Any, Depends(gov_welfare_service.get_welfare)]):
    return result


@limiter(max_requests=100)
@router.get("/static-params")
async def get_static_params(result: Annotated[Any, Depends(gov_welfare_service.get_welfare_id)]):
    return result
