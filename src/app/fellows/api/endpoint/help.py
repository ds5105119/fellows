from typing import Annotated

from fastapi import APIRouter, Depends

from src.app.fellows.api.dependencies import help_service
from src.app.fellows.schema.help import HelpsRead

router = APIRouter()


@router.get("", response_model=HelpsRead)
async def get_helps(helps: Annotated[HelpsRead, Depends(help_service.get_helps)]):
    return helps


@router.post("")
async def create_help(_: Annotated[None, Depends(help_service.create_help)]):
    return None


@router.put("")
async def update_help(_: Annotated[None, Depends(help_service.update_help)]):
    return None


@router.delete("/{id}")
async def delete_help(_: Annotated[None, Depends(help_service.delete_help)]):
    return None
