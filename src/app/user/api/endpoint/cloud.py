from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.app.user.api.dependencies import cloud_service
from src.app.user.schema.cloud import PresignedResponse

router = APIRouter()


@router.get("/object/presigned/get", response_model=PresignedResponse)
async def create_presigned_get_request(
    url: Annotated[PresignedResponse, Depends(cloud_service.create_get_presigned_url)],
):
    return url


@router.get("/object/presigned/put", response_model=PresignedResponse)
async def create_presigned_put_request(
    url: Annotated[PresignedResponse, Depends(cloud_service.create_put_presigned_url)],
):
    return url


@router.delete("/object", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(_: Annotated[None, Depends(cloud_service.delete_file)]):
    pass
