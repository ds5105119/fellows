from fastapi import APIRouter

from src.app.fellows.data import terms

router = APIRouter()


@router.get("/service/new/privacy", response_model=str)
async def get_privacy_terms():
    return terms.privacy


@router.get("/service/new/third", response_model=str)
async def get_privacy_terms():
    return terms.third_party
