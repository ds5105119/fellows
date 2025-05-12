from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.app.user.api.dependencies import cloud_service
from src.app.user.schema.cloud import PresignedPutResponse

router = APIRouter()


@router.get("/presigned/get", response_model=str)
async def create_presigned_get_request(
    url: Annotated[str, Depends(cloud_service.create_get_presigned_url)],
):
    return url


@router.get("/presigned/put", response_model=PresignedPutResponse)
async def create_presigned_put_request(
    url: Annotated[PresignedPutResponse, Depends(cloud_service.create_put_presigned_url)],
):
    return url


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(_: Annotated[None, Depends(cloud_service.delete_file)]):
    pass
