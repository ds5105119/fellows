from typing import Annotated

from fastapi import APIRouter, Depends

from src.app.fellows.api.dependencies import contact_service

router = APIRouter()


@router.post("/homepage")
async def create_help(_: Annotated[None, Depends(contact_service.create_contact)]):
    return None
