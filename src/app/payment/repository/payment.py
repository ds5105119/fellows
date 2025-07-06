from typing import Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.payment.model.payment import PaymentTransaction
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class PaymentTransactionCreateRepository(ABaseCreateRepository[PaymentTransaction]):
    pass


class PaymentTransactionReadRepository(ABaseReadRepository[PaymentTransaction]):
    async def get_by_ordr_idxx(self, session: AsyncSession, site_cd: str, ordr_idxx: str) -> PaymentTransaction | None:
        """
        가맹점 사이트 코드와 주문번호로 결제 트랜잭션 인스턴스를 조회합니다.
        결제 흐름에서 특정 주문을 찾아 업데이트할 때 사용됩니다.

        :param session: SQLAlchemy AsyncSession 객체
        :param site_cd: KCP 가맹점 사이트 코드
        :param ordr_idxx: 가맹점 주문번호
        :return: 조회된 PaymentTransaction 객체 또는 None
        """
        result = await self.get_instance(
            session,
            filters=[
                self.model.site_cd == site_cd,
                self.model.ordr_idxx == ordr_idxx,
            ],
        )
        return result.scalars().first()

    async def get_by_kcp_tno(self, session: AsyncSession, kcp_tno: str) -> PaymentTransaction | None:
        """
        KCP 거래 고유번호(tno)로 결제 트랜잭션 인스턴스를 조회합니다.
        취소 등의 후속 처리 시 사용될 수 있습니다.

        :param session: SQLAlchemy AsyncSession 객체
        :param kcp_tno: KCP 거래 고유번호
        :return: 조회된 PaymentTransaction 객체 또는 None
        """
        result = await self.get_instance(
            session,
            filters=[self.model.kcp_tno == kcp_tno],
        )
        return result.scalars().first()


class PaymentTransactionUpdateRepository(ABaseUpdateRepository[PaymentTransaction]):
    async def update_by_ordr_idxx(self, session: AsyncSession, site_cd: str, ordr_idxx: str, **kwargs: Any) -> int:
        """
        가맹점 사이트 코드와 주문번호로 특정 결제 트랜잭션을 업데이트합니다.

        :param session: SQLAlchemy AsyncSession 객체
        :param site_cd: KCP 가맹점 사이트 코드
        :param ordr_idxx: 가맹점 주문번호
        :param kwargs: 업데이트할 필드와 값
        :return: 업데이트된 행의 수
        """
        result = await self.update(
            session,
            filters=[
                self.model.site_cd == site_cd,
                self.model.ordr_idxx == ordr_idxx,
            ],
            **kwargs,
        )
        return result.scalars().first()


class PaymentTransactionDeleteRepository(ABaseDeleteRepository[PaymentTransaction]):
    pass


class PaymentTransactionRepository(
    PaymentTransactionCreateRepository,
    PaymentTransactionReadRepository,
    PaymentTransactionUpdateRepository,
    PaymentTransactionDeleteRepository,
):
    pass
