from datetime import timedelta
from logging import getLogger
from time import time
from typing import Annotated

import openai
from fastapi import Body, HTTPException, Path, Query, Request, status
from httpx import AsyncClient, HTTPError
from keycloak import KeycloakAdmin
from webtool.cache import RedisCache

from src.app.fellows.repository.contract import ContractRepository
from src.app.fellows.schema.contract import (
    CustomContractStatus,
    ERPNextContractRequest,
    NewContractCallbackRequest,
    UpdateERPNextContract,
    UpdateERPNextContractForInner,
    UserERPNextContract,
)
from src.app.user.repository.alert import AlertRepository
from src.app.user.schema.user_data import ProjectAdminUserAttributes, UserAttributes
from src.app.user.service.cloud import CloudService
from src.core.config import settings
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.infra import make_ncloud_signature_v2

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

        if contract.custom_contract_status == CustomContractStatus.UNSIGNED and data.is_signed == True:
            user_data = await self.keycloak_admin.a_get_user(project.customer)

            customer = ProjectAdminUserAttributes.model_validate(
                user_data["attributes"]
                | {
                    "email": user_data["email"],
                    "sub": user_data["id"],
                }
            )

            if not (
                customer.name
                and customer.birthdate
                and customer.email
                and customer.phoneNumber
                and customer.gender
                and customer.sub_locality
                and customer.street
            ):
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

            return await self.contract_repository.update_contract_by_id(
                contract.name,
                UpdateERPNextContractForInner.model_validate(
                    {
                        "custom_customer_name": customer.name[0],
                        "custom_customer_birthdate": customer.birthdate[0],
                        "custom_customer_email": customer.email[0],
                        "custom_customer_phone": customer.phoneNumber[0],
                        "custom_customer_gender": customer.gender[0],
                        "custom_customer_address": customer.street[0] + " " + customer.sub_locality[0],
                        **data.model_dump(exclude_unset=True),
                    }
                ),
            )

        return await self.contract_repository.update_contract_by_id(contract.name, data)

    async def send_biz_message(self, request: Request, to: list[str], data: dict):
        client: AsyncClient = request.app.requests_client

        service_id = settings.ncloud_api.biz_message_service_id
        uri = f"/alimtalk/v2/services/{service_id}/messages"

        timestamp = int(time() * 1000)
        timestamp = str(timestamp)

        signature = make_ncloud_signature_v2("POST", uri, timestamp)

        header = {
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": settings.ncloud_api.id,
            "x-ncp-apigw-signature-v2": signature,
        }

        data = {
            "plusFriendId": "@fellows",
            "templateCode": "contract",
            "messages": [
                {
                    "to": t,
                    **data,
                    "useSmsFailover": False,
                }
                for t in to
            ],
        }

        try:
            response = await client.post(
                "https://sens.apigw.ntruss.com" + uri,
                headers=header,
                json=data,
            )
            data = response.json()

            return data
        except HTTPError as e:
            logger.error(f"Failed to send email using SESv2: {e}")
            return False

    async def new_contract_callback(
        self,
        request: Request,
        body: Annotated[NewContractCallbackRequest, Body()],
    ):
        if body.secret_key != settings.secret_key:
            raise HTTPException(status_code=403)

        contract = await self.contract_repository.get_contract(body.name)
        user_data = await self.keycloak_admin.a_get_user(contract.party_name)
        user_attributes = UserAttributes.model_validate(
            user_data["attributes"]
            | {
                "email": user_data["email"],
                "sub": user_data["id"],
            }
        )
        project = await self.contract_repository.get_project_by_id(contract.document_name, user_attributes.sub)

        data = {
            "content": f"안녕하세요 {user_attributes.name[0]}님, 고객님이 의뢰하신 {project.custom_project_title}의 계약서가 도착하였습니다.",
            "headerContent": "계약서 서명 요청",
            "itemHighlight": {
                "title": f"{contract.custom_name}",
                "description": f"사인 전",
            },
            "item": {
                "list": [
                    {
                        "title": "계약 시작일",
                        "description": f"{contract.start_date}",
                    },
                    {
                        "title": "계약 종료일",
                        "description": f"{contract.end_date}",
                    },
                    {
                        "title": "계약 금액",
                        "description": f"{contract.custom_fee} 원",
                    },
                    {
                        "title": "서명 요청자",
                        "description": "IIH(contact@iihus.com)",
                    },
                    {
                        "title": "서명 가능일",
                        "description": f"{contract.start_date - timedelta(days=1)} 까지",
                    },
                ],
            },
            "buttons": [
                {
                    "type": "WL",
                    "name": "서명하기",
                    "linkMobile": f"https://www.iihus.com/service/project/contracts/{contract.name}",
                    "linkPc": f"https://www.iihus.com/service/project/contracts/{contract.name}",
                }
            ],
        }

        await self.send_biz_message(request, user_attributes.phoneNumber, data)
