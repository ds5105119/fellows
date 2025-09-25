from logging import getLogger
from random import randint
from time import time
from typing import Annotated

from botocore.exceptions import ClientError
from fastapi import HTTPException, Path, Query, Request, status
from httpx import AsyncClient, HTTPError
from keycloak import KeycloakAdmin
from mypy_boto3_sesv2 import SESV2Client
from webtool.cache import RedisCache

from src.app.user.schema.user_data import *
from src.core.config import settings
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.infra import make_ncloud_signature_v2

logger = getLogger(__name__)


def _create_verification_biz_message(
    to: list[str],
    content: str,
):
    timestamp = int(time() * 1000)
    timestamp = str(timestamp)

    header = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": settings.ncloud_api.id,
        "x-ncp-apigw-signature-v2": make_ncloud_signature_v2(timestamp),
    }

    data = {
        "plusFriendId": "@fellows",
        "templateCode": "otp",
        "messages": [
            {
                "to": t,
                "content": content,
                "useSmsFailover": False,
            }
            for t in to
        ],
    }

    return header, data


def _create_verification_email_body(otp: str):
    """인증 이메일의 HTML 및 텍스트 본문을 생성합니다."""

    body_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; padding: 40px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header img {{ max-width: 150px; }}
            .content {{ text-align: center; }}
            .content h1 {{ color: #333; font-size: 24px; }}
            .content p {{ color: #555; font-size: 16px; line-height: 1.6; }}
            .otp-box {{ background-color: #f0f8ff; border: 1px dashed #add8e6; padding: 20px; margin: 30px 0; border-radius: 5px; }}
            .otp-code {{ font-size: 36px; font-weight: bold; color: #0056b3; letter-spacing: 5px; }}
            .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://www.fellows.my/fellows/logo.svg" alt="Fellows Logo">
            </div>
            <div class="content">
                <h1>이메일 주소 인증 안내</h1>
                <p>이메일 주소를 확인하기 전 거쳐야 할 간단한 단계가 하나 있습니다.</p>
                <p>아래 코드를 입력하여 인증을 완료해 주세요.</p>
                <div class="otp-box">
                    <p style="font-size:14px; margin:0 0 10px 0; color:#555;">인증 코드</p>
                    <div class="otp-code">{otp}</div>
                </div>
                <p>이 코드는 2시간 동안 유효합니다.</p>
                <p>본인이 요청하지 않은 경우, 이 이메일을 무시해 주세요.</p>
            </div>
            <div class="footer">
                <p>© 2024 Fellows. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # 일반 텍스트 본문 (HTML을 지원하지 않는 클라이언트용)
    body_text = f"""
    이메일 주소를 확인하기 전 거쳐야 할 간단한 단계가 하나 있습니다.
    아래 코드를 입력하여 인증을 완료해 주세요.

    인증 코드: {otp}

    이 코드는 2시간 동안 유효합니다.
    본인이 요청하지 않은 경우, 이 이메일을 무시해 주세요.

    감사합니다.
    Fellows 드림
    """

    return body_html, body_text


class UserDataService:
    def __init__(
        self,
        keycloak_admin: KeycloakAdmin,
        redis_cache: RedisCache,
        ses_client: SESV2Client,
    ):
        self.keycloak_admin = keycloak_admin
        self.redis_cache = redis_cache
        self.ses_client = ses_client

        """
        유저의 데이터를 관리하는 서비스
        
        Args:
            base_url (str):
            swagger_url (str):
            api_key (str):
            paths (dict):
            batch_size (int):
            timeout (int):
            api_config (ApiConfig):
        """

    async def read_users(self, _: get_current_user, sub: Annotated[list[str], Query()]):
        search_query = "id:" + " ".join(sub)
        users = await self.keycloak_admin.a_get_users({"search": search_query})
        return [
            ExternalUserAttributes.model_validate(
                data["attributes"]
                | {
                    "email": data["email"],
                    "sub": data["id"],
                }
            )
            for data in users
        ]

    async def read_user(self, user: get_current_user, sub: str = Path()):
        data = await self.keycloak_admin.a_get_user(sub)

        if user.sub == sub:
            return UserAttributes.model_validate(
                data["attributes"]
                | {
                    "email": data["email"],
                    "sub": data["id"],
                }
            )
        return ExternalUserAttributes.model_validate(
            data["attributes"]
            | {
                "email": data["email"],
                "sub": data["id"],
            }
        )

    async def update_user(
        self,
        data: UpdateUserAttributes,
        user: get_current_user,
    ):
        payload = await self.keycloak_admin.a_get_user(user.sub)
        attributes = data.model_dump(exclude_unset=True, exclude={"email"})
        payload["attributes"].update(attributes)

        await self.keycloak_admin.a_update_user(user_id=user.sub, payload=payload)
        return await self.keycloak_admin.a_get_user(user.sub)

    async def send_biz_message(self, request: Request, header: dict, body: dict):
        client: AsyncClient = request.app.requests_client
        service_id = settings.ncloud_api.biz_message_service_id

        try:
            response = await client.post(
                f"https://sens.apigw.ntruss.com/alimtalk/v2/services/{service_id}/messages",
                headers=header,
                data=body,
            )
            data = response.json()

            return data
        except HTTPError as e:
            logger.error(f"Failed to send email using SESv2: {e}")
            return False

    async def send_email(self, to_email: str, subject: str, body_text: str, body_html: str):
        try:
            response = self.ses_client.send_email(
                FromEmailAddress="noreply@iihus.com",
                Destination={"ToAddresses": [to_email]},
                Content={
                    "Simple": {
                        "Subject": {
                            "Data": subject,
                            "Charset": "UTF-8",
                        },
                        "Body": {
                            "Text": {
                                "Data": body_text,
                                "Charset": "UTF-8",
                            },
                            "Html": {
                                "Data": body_html,
                                "Charset": "UTF-8",
                            },
                        },
                    }
                },
            )
            logger.info(f"Email sent via SESv2! Message ID: {response['MessageId']}")
            return True
        except ClientError as e:
            logger.error(f"Failed to send email using SESv2: {e.response['Error']['Message']}")
            return False

    async def update_phone_number_by_biz_message_request(
        self,
        request: Request,
        data: PhoneNumberUpdateRequest,
        user: get_current_user,
    ):
        existing_user = await self.keycloak_admin.a_get_users({"phoneNumber": data.phone_number})
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        otp = f"{randint(0, 999999):06d}"
        await self.redis_cache.set(f"{user.sub}{data.phone_number}-phone_number_update_request", otp, 60 * 60 * 2)

        subject = f"\n\n인증번호는 {otp} 입니다"
        header, body = _create_verification_biz_message(to=[data.phone_number], content=subject)

        biz_message_sent = await self.send_biz_message(request, header, body)

        if not biz_message_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="인증 메시지 발송에 실패했습니다. 잠시 후 다시 시도해주세요.",
            )

    async def update_email_request(
        self,
        data: EmailUpdateRequest,
        user: get_current_user,
    ):
        existing_user = await self.keycloak_admin.a_get_users({"email": data.email})
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        otp = f"{randint(0, 999999):06d}"
        await self.redis_cache.set(f"{user.sub}{data.email}", otp, 60 * 60 * 2)

        subject = f"Fellows 인증 코드는 {otp} 입니다."
        body_html, body_text = _create_verification_email_body(otp)

        email_sent = await self.send_email(
            to_email=str(data.email),
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )

        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="인증 이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.",
            )

    async def update_email_verify(
        self,
        data: EmailUpdateVerify,
        user: get_current_user,
    ):
        otp = await self.redis_cache.get(f"{user.sub}{data.email}")

        if otp.decode() != data.otp:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        existing_user = await self.keycloak_admin.a_get_users({"email": data.email})
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        payload = await self.keycloak_admin.a_get_user(user.sub)
        payload["email"] = data.email

        await self.keycloak_admin.a_update_user(user_id=user.sub, payload=payload)
        return await self.keycloak_admin.a_get_user(user.sub)

    async def update_address_kakao(
        self,
        data: KakaoAddressDto,
        user: get_current_user,
    ):
        if data.meta.total_count == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        oidc_address = OIDCAddressDto(
            location=data.location,
            postal_code=data.documents[0].road_address.zone_no,
            region=data.documents[0].road_address.region_1depth_name,
            locality=data.documents[0].road_address.region_2depth_name,
            sub_locality=data.documents[0].address.region_3depth_name,
            country="kr",
            street=data.documents[0].road_address.address_name,
            formatted=data.documents[0].address.address_name,
        )

        payload = await self.keycloak_admin.a_get_user(user.sub)
        payload["attributes"].update(oidc_address.model_dump())

        await self.keycloak_admin.a_update_user(user_id=user.sub, payload=payload)
