from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.app.user.api.dependencies import cloud_service
from src.app.user.schema.cloud import *

router = APIRouter()


@router.get("/object/presigned/get", response_model=str)
async def create_presigned_get_request(
    url: Annotated[str, Depends(cloud_service.create_get_presigned_url)],
):
    return url


@router.get("/object/presigned/put", response_model=PresignedPutResponse)
async def create_presigned_put_request(
    url: Annotated[PresignedPutResponse, Depends(cloud_service.create_put_presigned_url)],
):
    return url


@router.get("/object/presigned/put/fellows", response_model=PresignedPutResponse)
async def create_presigned_put_request_for_fellows(
    url: Annotated[PresignedPutResponse, Depends(cloud_service.create_put_presigned_url)],
):
    return url


@router.get("/object/presigned/get/sse/c", response_model=SSECPresignedResponse)
async def create_sse_c_presigned_get_request(
    url: Annotated[SSECPresignedResponse, Depends(cloud_service.create_sse_c_get_presigned_url)],
):
    return url


@router.get("/object/presigned/put/sse/c", response_model=SSECPresignedResponse)
async def create_sse_c_presigned_put_request(
    url: Annotated[SSECPresignedResponse, Depends(cloud_service.create_sse_c_put_presigned_url)],
):
    return url


@router.delete("/object", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(_: Annotated[None, Depends(cloud_service.delete_file)]):
    pass
