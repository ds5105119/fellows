from typing import Annotated

from fastapi import APIRouter, Depends, status
from webtool.throttle import limiter

from src.app.user.api.dependencies import user_data_service
from src.app.user.schema.user_data import UserAttributes

router = APIRouter()


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


@limiter(1, 20)
@router.post("/phone")
async def update_phone_number_by_biz_message(
    _: Annotated[None, Depends(user_data_service.update_phone_number_by_biz_message_request)],
):
    pass


@limiter(1, 2)
@router.post("/email")
async def update_email_request(_: Annotated[None, Depends(user_data_service.update_email_request)]):
    pass


@limiter(1, 2)
@router.post("/email/verify")
async def update_email_verify(_: Annotated[None, Depends(user_data_service.update_email_verify)]):
    pass
