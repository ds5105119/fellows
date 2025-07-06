from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class PaymentStartRequest(BaseModel):
    good_mny: int = Field(description="결제 금액")
    pay_method: Literal["CARD", "BANK"] = Field(description="결제 수단 코드")
    good_name: str = Field(description="상품명")
    user_agent: str | None = Field(default=None, description="클라이언트 User-Agent")


class TransactionRegistrationRequest(BaseModel):
    site_cd: str = Field(description="가맹점 ID (영문대문자+숫자 5자리)")
    ordr_idxx: str = Field(description="가맹점 주문번호")
    good_mny: int = Field(description="결제 금액")
    pay_method: Literal["CARD", "BANK"] = Field(description="결제 수단 코드")
    good_name: str = Field(description="상품명")
    Ret_URL: HttpUrl = Field(description="결제 후 리턴 URL")
    user_agent: str | None = Field(default=None, description="클라이언트 User-Agent")
    server: Literal["true", "false"] | None = Field(default="false", description="서버 여부")


class TransactionRegistrationResponse(BaseModel):
    Code: str = Field(description="응답 코드, 정상인 경우 0000")
    Message: str = Field(description="응답 메시지")
    approvalKey: str = Field(description="거래 인 키")
    PayUrl: HttpUrl = Field(description="결제 페이지 URL")
    hashData: str = Field(description="거래 등록 해시 데이터")
    traceNo: str = Field(description="거래 등록 추적 번호")
    paymentMethod: str = Field(description="결제 수단")
    request_URI: str | None = Field(default=None, description="요청 URI")


class PaymentAuthResponse(BaseModel):
    site_cd: str = Field(description="가맹점 ID (영문대문자+숫자 5자리)")
    enc_data: str = Field(description="결제창 인증결과 암호화 정보 (변경 금지)")
    enc_info: str = Field(description="결제창 인증결과 암호화 정보 (변경 금지)")
    tran_cd: str = Field(description="요청 코드 (고정값 8자리)")
    ordr_idxx: str = Field(description="상점 주문번호 (최대 70자, 유니크 권장)")
    buyr_name: str | None = Field(default=None, description="주문자 이름 (최대 40자)")
    buyr_mail: str | None = Field(default=None, description="주문자 이메일 (최대 100자)")
    buyr_tel2: str | None = Field(default=None, description="주문자 휴대폰번호 (하이픈 포함 가능, 최대 20자)")


class PaymentRequest(BaseModel):
    site_cd: str = Field(description="가맹점 ID (영문대문자+숫자 5자리)")
    kcp_cert_info: str = Field(description="서비스 인증서 (PEM 직렬화 문자열)")
    enc_data: str = Field(description="결제창 인증결과 암호화 정보")
    enc_info: str = Field(description="결제창 인증결과 암호화 정보")
    tran_cd: str = Field(description="요청 코드 (고정값 8자리)")
    ordr_mony: int = Field(description="결제 요청 금액 (최대 9자리 숫자)")
    ordr_no: str = Field(description="실제 결제 주문번호 (최대 40자)")
    pay_type: Literal["PACA", "PABK"] = Field(description="결제 수단 코드")


class PaymentResponse(BaseModel):
    res_cd: str = Field(description="결과 코드 (정상: 0000)")
    res_msg: str = Field(description="결과 메시지")
    res_en_msg: str | None = Field(default=None, description="영문 결과 메시지")
    pay_method: Literal["PACA", "PABK", "PAPT", "PAMC", "PATK", "PAKM", "PANP"] = Field(description="응답 결제 수단")
    tno: str = Field(description="NHN KCP 거래 고유번호 (14자리)")
    amount: int = Field(description="최종 결제 금액")
    card_other_pay_type: (
        Literal[
            "OT12",  # 페이코
            "OT01",  # 삼성페이
            "OT03",  # SSG페이
            "OT11",  # L.PAY
            "OT13",  # 카카오페이
            "OT16",  # 네이버페이
            "OT21",  # 애플페이
            "OT23",  # 토스페이
        ]
        | None
    ) = Field(default=None, description="제휴간편결제 유형")
