from logging import getLogger
from typing import Annotated

import openai
from fastapi import HTTPException, Path, Query, status
from keycloak import KeycloakAdmin
from webtool.cache import RedisCache

from src.app.fellows.repository.contract import ContractRepository
from src.app.fellows.schema.contract import (
    ERPNextContractRequest,
    UpdateERPNextContract,
    UserERPNextContract,
)
from src.app.user.repository.alert import AlertRepository
from src.app.user.service.cloud import CloudService
from src.core.dependencies.auth import get_current_user

logger = getLogger(__name__)


class ContrctService:
    def __init__(
        self,
        openai_client: openai.AsyncOpenAI,
        cloud_service: CloudService,
        contract_repository: ContractRepository,
        alert_repository: AlertRepository,
        keycloak_admin: KeycloakAdmin,
        redis_cache: RedisCache,
    ):
        self.openai_client = openai_client
        self.cloud_service = cloud_service
        self.contract_repository = contract_repository
        self.alert_repository = alert_repository
        self.keycloak_admin = keycloak_admin
        self.redis_cache = redis_cache

    async def get_contract(self, user: get_current_user, contract_id: str = Path()) -> UserERPNextContract:
        contract = await self.contract_repository.get_contract(contract_id)

        if not contract.document_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update issues in this project.",
            )

        project, level = await self.contract_repository.get_user_project_permission(contract.document_name, user.sub)

        if level > 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update issues in this project.",
            )

        return contract

    async def get_contracts(
        self,
        data: Annotated[ERPNextContractRequest, Query()],
        user: get_current_user,
    ):
        """
        사용자의 계약서 목록을 조회합니다.

        Args:
            data: 페이지네이션 및 필터링 옵션.
            user: 현재 인증된 사용자 정보. 권한 레벨 0-3의 프로젝트만 조회됩니다.

        Returns:
            계약서 목록과 페이지네이션 정보.
        """
        return await self.contract_repository.get_contracts(data, user.sub)

    async def update_contracts(
        self,
        data: UpdateERPNextContract,
        user: get_current_user,
        contract_id: str = Path(),
    ):
        """
        사용자의 계약서를 업데이트합니다

        Args:
            data: 업데이트할 계약서 정보
            user: 현재 인증된 사용자 정보. 계약자이면서 어드민 이상만 사인할 수 있습니다.
            contract_id: 계약서 번호

        Returns:
            None
        """
        contract = await self.contract_repository.get_contract(contract_id)

        if not contract.document_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update issues in this project.",
            )

        project, level = await self.contract_repository.get_user_project_permission(contract.document_name, user.sub)

        if project.customer != user.sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update the contracts.",
            )

        return await self.contract_repository.update_contract_by_id(contract.name, data)
