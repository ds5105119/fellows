from typing import Annotated

from fastapi import APIRouter, Depends

from src.app.payment.api.dependencies import payment_service
from src.app.payment.schema.payment import PaymentResponse, TransactionRegistrationResponse

router = APIRouter()


@router.post("/start")
async def start_payment(response: Annotated[TransactionRegistrationResponse, Depends(payment_service.start_payment)]):
    return response


@router.post("/callback")
async def approve_payment(response: Annotated[PaymentResponse, Depends(payment_service.approve_payment)]):
    return response
