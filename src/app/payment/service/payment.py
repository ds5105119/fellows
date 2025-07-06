# src/app/payment/service.py

import uuid

import httpx
from fastapi import HTTPException, Request, status

from src.app.payment.model.payment import *
from src.app.payment.repository.payment import *
from src.app.payment.schema.payment import *
from src.core.config import settings
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session


class PaymentService:
    def __init__(self, repository: PaymentTransactionRepository):
        """
        NHN KCP 결제 관련 로직을 처리하는 서비스 (백엔드 거래등록 포함)

        Args:
            repository (PaymentTransactionRepository): 결제 트랜잭션 DB 레포지토리
        """
        self.repository = repository
        self.site_cd = settings.kcp.site_id
        self.cert_info = settings.kcp.cert_info

        self.mobile_reg_url = "https://testpay.kcp.co.kr/"
        self.payment_url = "https://stg-spl.kcp.co.kr/gw/enc/v1/payment"

    async def _get_transaction_or_404(self, session: AsyncSession, ordr_idxx: str) -> PaymentTransaction:
        """주문번호로 트랜잭션을 조회하고 없으면 404 에러를 발생시키는 헬퍼 함수"""
        transaction = await self.repository.get_by_ordr_idxx(session, self.site_cd, ordr_idxx)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"주문번호 '{ordr_idxx}'에 해당하는 결제 정보를 찾을 수 없습니다.",
            )
        return transaction

    async def start_payment(
        self,
        request: Request,
        data: PaymentStartRequest,
        session: postgres_session,
        user: get_current_user,
    ) -> TransactionRegistrationResponse:
        """
        [1단계] 결제 거래를 등록하고, 프론트엔드로 결제창 호출 정보를 반환합니다.
        - DB에 PENDING 상태의 결제 트랜잭션을 생성합니다.
        - KCP 거래등록 API를 호출합니다.
        """
        # 1. 고유한 주문번호 생성
        ordr_idxx = f"ORDER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        # 2. DB에 결제 트랜잭션 기록 (상태: PENDING)
        await self.repository.create(
            session,
            sub=user.sub,
            site_cd=self.site_cd,
            ordr_idxx=ordr_idxx,
            good_name=data.good_name,
            initial_amount=data.good_mny,
            pay_method=data.pay_method,
            buyer_name=user.name or user.username,
            buyer_email=user.email,
            buyer_phone=user.phone,
            status=PaymentStatus.PENDING,
        )

        # 3. KCP 거래등록 API 요청 데이터 준비
        kcp_reg_req_payload = {
            "site_cd": self.site_cd,
            "ordr_idxx": ordr_idxx,
            "pay_method": data.pay_method,
            "good_name": data.good_name,
            "good_mny": str(data.good_mny),
            "Ret_URL": f"{settings.base_url}/payment/kcp-return",
        }

        # 4. KCP 거래등록 API 호출
        client = request.app.requests_client
        try:
            response = await client.post(self.mobile_reg_url, json=kcp_reg_req_payload)
            response.raise_for_status()
            kcp_response_data = response.json()

            # Pydantic 모델로 유효성 검사 및 객체화
            reg_response = TransactionRegistrationResponse.model_validate(kcp_response_data)

            if reg_response.Code != "0000":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"KCP 거래등록 실패: [{reg_response.Code}] {reg_response.Message}",
                )

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"KCP API 통신 오류: {e.response.text}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"KCP 응답 처리 중 오류 발생: {str(e)}"
            )

        await self.repository.update_by_ordr_idxx(session, self.site_cd, ordr_idxx, kcp_trace_no=reg_response.traceNo)

        return reg_response

    async def approve_payment(
        self,
        request: Request,
        data: PaymentAuthResponse,
        session: postgres_session,
    ) -> PaymentResponse:
        """
        [3단계] KCP 결제창 인증 후, 백엔드에서 최종 결제 승인을 요청하고 결과를 처리합니다.
        """
        # 1. DB에서 원거래 정보 조회 및 검증
        transaction = await self._get_transaction_or_404(session, data.ordr_idxx)

        if transaction.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="이미 처리되었거나 유효하지 않은 결제 요청입니다."
            )

        # 2. 결제 요청 API에 보낼 데이터 구성
        kcp_req_data = {
            "tran_cd": data.tran_cd,
            "site_cd": self.site_cd,
            "kcp_cert_info": self.cert_info,
            "enc_data": data.enc_data,
            "enc_info": data.enc_info,
            "ordr_mony": str(transaction.initial_amount),
            "ordr_no": transaction.ordr_idxx,
            "pay_type": transaction.pay_method,  # DB에 저장된 'PACA', 'PABK' 사용
        }

        # 3. KCP 결제 승인 API 호출
        client = request.app.requests_client
        try:
            response = await client.post(self.payment_url, json=kcp_req_data)
            response.raise_for_status()
            payment_result = PaymentResponse.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            await self.repository.update_by_ordr_idxx(
                session,
                self.site_cd,
                data.ordr_idxx,
                status=PaymentStatus.FAILED,
                res_msg=f"KCP API 통신 오류: {e.response.status_code}",
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"KCP API 통신 오류: {e.response.text}")
        except Exception as e:
            await self.repository.update_by_ordr_idxx(
                session, self.site_cd, data.ordr_idxx, status=PaymentStatus.FAILED, res_msg=f"응답 처리 오류: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"KCP 응답 처리 중 오류 발생: {e}"
            )

        # 4. KCP 응답 결과에 따라 DB 업데이트
        if payment_result.res_cd == "0000":
            update_data = {
                "status": PaymentStatus.PAID,
                "kcp_tno": payment_result.tno,
                "final_amount": payment_result.amount,
                "res_cd": payment_result.res_cd,
                "res_msg": payment_result.res_msg,
                "easy_payment_type": payment_result.card_other_pay_type,
                "paid_at": datetime.now(),
                # TODO: 여기에 카드/은행 등 결제수단별 상세 정보를 추가
            }
            await self.repository.update_by_ordr_idxx(session, self.site_cd, data.ordr_idxx, **update_data)
        else:
            await self.repository.update_by_ordr_idxx(
                session,
                self.site_cd,
                data.ordr_idxx,
                status=PaymentStatus.FAILED,
                kcp_tno=payment_result.tno,
                res_cd=payment_result.res_cd,
                res_msg=payment_result.res_msg,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"결제 실패: [{payment_result.res_cd}] {payment_result.res_msg}",
            )

        return payment_result
