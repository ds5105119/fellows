import base64
import hashlib
import hmac
import logging
import secrets
from typing import Annotated
from uuid import uuid4

from botocore.client import ClientError
from fastapi import Header, HTTPException, Query, Response, status
from mypy_boto3_s3 import S3Client
from sqlalchemy.exc import IntegrityError

from src.app.user.repository.cloud import FileRecordRepository
from src.app.user.schema.cloud import PresignedGetRequest, PresignedHeader, PresignedPutRequest, PresignedPutResponse
from src.core.config import settings
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session

logger = logging.getLogger(__name__)


class CloudService:
    def __init__(
        self,
        file_record_repository: FileRecordRepository,
        client: S3Client,
    ):
        self.file_record_repository = file_record_repository
        self.client = client

    def generate_sse_c_headers(self, key_length: int = 128):
        key = secrets.token_urlsafe(key_length)
        md5 = base64.b64encode(hashlib.md5(key.encode()).digest()).decode("utf-8")

        return {
            "SSECustomerAlgorithm": "AES256",
            "SSECustomerKey": key,
            "SSECustomerKeyMD5": md5,
        }

    def get_presigned_url(self, method: str, key: str, expires: int, headers: dict[str, str]):
        try:
            response = self.client.generate_presigned_url(
                method,
                Params={
                    "Bucket": settings.cloudflare.storage_bucket_name,
                    "Key": key,
                    **headers,
                },
                ExpiresIn=expires,
            )
        except ClientError as e:
            logging.error(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return response

    async def create_put_presigned_url(
        self,
        response: Response,
        user: get_current_user,
        session: postgres_session,
        data: Annotated[PresignedPutRequest, Query()],
    ) -> PresignedPutResponse:
        key = f"{data.suffix}{uuid4()}"
        headers = self.generate_sse_c_headers()
        presigned_url = self.get_presigned_url("get_object", key, 600, headers)

        try:
            await self.file_record_repository.create(
                session,
                key=key,
                sub=user.sub,
                sse_key=headers.get("SSECustomerKey"),
            )

        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Unknown error")

        response.headers["x-amz-server-side-encryption-customer-algorithm"] = headers.get("SSECustomerAlgorithm")
        response.headers["x-amz-server-side-encryption-customer-key"] = headers.get("SSECustomerKey")
        response.headers["x-amz-server-side-encryption-customer-key-MD5"] = headers.get("SSECustomerKeyMD5")

        return PresignedPutResponse(
            presigned_url=presigned_url,
            algorithm="AES256",
            key=key,
            sse_key=headers.get("SSECustomerKey"),
            md5=headers.get("SSECustomerKeyMD5"),
        )

    async def create_get_presigned_url(
        self,
        user: get_current_user,
        data: Annotated[PresignedGetRequest, Query()],
        headers: Annotated[PresignedHeader, Header()],
    ) -> str:
        algorithm = data.algorithm or headers.x_amz_server_side_encryption_customer_algorithm
        key = data.sse_key or headers.x_amz_server_side_encryption_customer_key

        if not algorithm or not key:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

        md5 = base64.b64encode(hashlib.md5(key.encode()).digest()).decode("utf-8")

        headers = {
            "SSECustomerAlgorithm": algorithm,
            "SSECustomerKey": key,
            "SSECustomerKeyMD5": md5,
        }

        return self.get_presigned_url("put_object", data.key, 3600, headers)

    async def delete_file(
        self,
        user: get_current_user,
        session: postgres_session,
        data: Annotated[PresignedGetRequest, Query()],
    ) -> None:
        result = await self.file_record_repository.get_instance(
            session,
            filters=[self.file_record_repository.model.key == data.key],
        )

        file_record = result.one_or_none()
        if file_record is None:
            raise HTTPException(status_code=404)
        file_record = file_record[0]

        if not hmac.compare_digest(file_record.sse_key, data.sse_key):
            raise HTTPException(status_code=403, detail="Invalid key")

        try:
            self.client.delete_object(
                Bucket=settings.cloudflare.storage_bucket_name,
                Key=data.key,
            )
        except ClientError as e:
            logger.error("Cloudflare delete error: %s", e)
            raise HTTPException(status_code=500, detail="Deletion failed")
