from typing import Annotated

from fastapi import APIRouter, Depends, status
from webtool.throttle import limiter

from src.app.user.api.dependencies import user_data_service
from src.app.user.schema.user_data import UserAttributes

router = APIRouter()


@router.post("/welfare/personal", status_code=status.HTTP_201_CREATED)
async def create_user_data(_: Annotated[None, Depends(user_data_service.create_user_data)]):
    pass


@router.get("/welfare/personal", status_code=status.HTTP_200_OK)
async def read_user_data(user_data: Annotated[None, Depends(user_data_service.read_user_data)]):
    return user_data


@router.put("/welfare/personal", status_code=status.HTTP_200_OK)
async def update_user_data(_: Annotated[None, Depends(user_data_service.update_user_data)]):
    pass


@router.post("/welfare/business", status_code=status.HTTP_201_CREATED)
async def create_business_data(_: Annotated[None, Depends(user_data_service.create_business_data)]):
    pass


@router.get("/welfare/business", status_code=status.HTTP_200_OK)
async def read_business_data(business_data: Annotated[None, Depends(user_data_service.read_business_data)]):
    return business_data


@router.put("/welfare/business", status_code=status.HTTP_200_OK)
async def update_business_data(_: Annotated[None, Depends(user_data_service.update_business_data)]):
    pass


@router.get("")
async def read_users(users: Annotated[UserAttributes, Depends(user_data_service.read_users)]):
    return users


@router.get("/{sub}")
async def read_user(user: Annotated[UserAttributes, Depends(user_data_service.read_user)]):
    return user


@router.put("", status_code=status.HTTP_200_OK)
async def update_user(user: Annotated[UserAttributes, Depends(user_data_service.update_user)]):
    return user


@router.put("/address/kakao", status_code=status.HTTP_200_OK)
async def update_address_kakao(_: Annotated[None, Depends(user_data_service.update_address_kakao)]):
    pass


@limiter(1, 2)
@router.post("/email")
async def update_email_request(_: Annotated[None, Depends(user_data_service.update_email_request)]):
    pass


@limiter(1, 2)
@router.post("/email/verify")
async def update_email_verify(_: Annotated[None, Depends(user_data_service.update_email_verify)]):
    pass
