from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.app.user.api.dependencies import user_data_service

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user_data(_: Annotated[None, Depends(user_data_service.create_user_data)]):
    pass


@router.get("", status_code=status.HTTP_200_OK)
async def read_user_data(user_data: Annotated[None, Depends(user_data_service.read_user_data)]):
    return user_data


@router.patch("", status_code=status.HTTP_200_OK)
async def update_user_data(_: Annotated[None, Depends(user_data_service.update_user_data)]):
    pass


@router.post("/business", status_code=status.HTTP_201_CREATED)
async def create_business_data(_: Annotated[None, Depends(user_data_service.create_business_data)]):
    pass


@router.get("/business", status_code=status.HTTP_200_OK)
async def read_business_data(business_data: Annotated[None, Depends(user_data_service.read_business_data)]):
    return business_data


@router.patch("/business", status_code=status.HTTP_200_OK)
async def update_business_data(_: Annotated[None, Depends(user_data_service.update_business_data)]):
    pass


@router.patch("/address", status_code=status.HTTP_200_OK)
async def update_address_oidc(_: Annotated[None, Depends(user_data_service.update_address_oidc)]):
    pass


@router.patch("/address/kakao", status_code=status.HTTP_200_OK)
async def update_address_kakao(_: Annotated[None, Depends(user_data_service.update_address_kakao)]):
    pass
