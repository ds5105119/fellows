import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base


# --- 결제 상태를 관리하기 위한 Enum ---
class PaymentStatus(enum.Enum):
    """결제 트랜잭션의 상태를 나타내는 열거형"""

    PENDING = "pending"  # 결제 대기 중
    PAID = "paid"  # 결제 완료
    FAILED = "failed"  # 결제 실패
    CANCELLED = "cancelled"  # 결제 취소


class PaymentTransaction(Base):
    """
    NHN KCP 결제 트랜잭션 정보를 저장하는 테이블.
    결제 요청부터 최종 응답까지의 모든 과정을 추적합니다.
    """

    __tablename__ = "payment_transactions"

    # --- 기본 정보 ---
    id: Mapped[int] = mapped_column(primary_key=True, comment="고유 식별자 (PK)")
    sub: Mapped[int] = mapped_column(String, unique=True, nullable=False)

    site_cd: Mapped[str] = mapped_column(String(10), nullable=False, comment="KCP 가맹점 사이트 코드 (T0000)")
    ordr_idxx: Mapped[str] = mapped_column(
        String(70), nullable=False, index=True, comment="가맹점 주문번호 (고유해야 함)"
    )

    # --- 가맹점 초기 주문 정보 ---
    good_name: Mapped[str] = mapped_column(String(100), comment="상품명")
    initial_amount: Mapped[int] = mapped_column(Integer, comment="최초 요청된 결제 금액 (good_mny)")
    buyer_name: Mapped[Optional[str]] = mapped_column(String(40), comment="주문자 이름")
    buyer_email: Mapped[Optional[str]] = mapped_column(String(100), comment="주문자 이메일")
    buyer_phone: Mapped[Optional[str]] = mapped_column(String(20), comment="주문자 휴대폰 번호")

    # --- 결제 상태 및 KCP 중간 정보 ---
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
        comment="결제 상태 (pending, paid, failed, cancelled)",
    )
    kcp_trace_no: Mapped[Optional[str]] = mapped_column(String(100), comment="KCP 거래등록 추적번호 (traceNo)")

    # --- KCP 최종 결제 응답 공통 정보 ---
    kcp_tno: Mapped[Optional[str]] = mapped_column(
        String(30), unique=True, index=True, comment="KCP 거래 고유번호 (tno)"
    )
    final_amount: Mapped[Optional[int]] = mapped_column(Integer, comment="최종 결제된 금액 (amount)")
    pay_method: Mapped[Optional[str]] = mapped_column(String(10), comment="최종 결제 수단 (PACA, PABK 등)")
    res_cd: Mapped[Optional[str]] = mapped_column(String(4), comment="KCP 응답 코드 (res_cd)")
    res_msg: Mapped[Optional[str]] = mapped_column(String(200), comment="KCP 응답 메시지 (res_msg)")
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="결제 완료 시각 (app_time)")

    # --- 신용카드 결제 응답 정보 (nullable) ---
    card_cd: Mapped[Optional[str]] = mapped_column(String(10), comment="카드사 코드")
    card_name: Mapped[Optional[str]] = mapped_column(String(32), comment="카드사 이름")
    card_no_masked: Mapped[Optional[str]] = mapped_column(String(20), comment="마스킹된 카드번호")
    card_app_no: Mapped[Optional[str]] = mapped_column(String(20), comment="카드 승인번호")
    card_quota: Mapped[Optional[str]] = mapped_column(String(2), comment="할부 개월 (00: 일시불)")
    is_interest_free: Mapped[Optional[bool]] = mapped_column(Boolean, comment="무이자 할부 여부 (Y/N)")

    # [추가된 컬럼]
    easy_payment_type: Mapped[Optional[str]] = mapped_column(
        String(10), comment="제휴간편결제 유형 코드 (KCP: card_other_pay_type)"
    )

    # --- 계좌이체 결제 응답 정보 (nullable) ---
    bank_code: Mapped[Optional[str]] = mapped_column(String(10), comment="은행 코드")
    bank_name: Mapped[Optional[str]] = mapped_column(String(20), comment="은행 이름")
    cash_receipt_no: Mapped[Optional[str]] = mapped_column(String(30), comment="현금영수증 거래번호 (cash_no)")
    cash_receipt_auth_no: Mapped[Optional[str]] = mapped_column(String(20), comment="현금영수증 승인번호 (cash_authno)")

    # --- 타임스탬프 ---
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="레코드 생성 시각")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="레코드 마지막 수정 시각"
    )

    # --- 복합 제약 조건 ---
    __table_args__ = (UniqueConstraint("site_cd", "ordr_idxx", name="uq_site_cd_ordr_idxx"),)

    def __repr__(self) -> str:
        return (
            f"<PaymentTransaction(id={self.id}, ordr_idxx='{self.ordr_idxx}', "
            f"status='{self.status.value}', kcp_tno='{self.kcp_tno}')>"
        )
