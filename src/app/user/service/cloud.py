import base64
import hashlib
import logging
import os
from typing import Annotated
from uuid import uuid4

from botocore.client import ClientError
from fastapi import Header, HTTPException, Query, Response, status
from mypy_boto3_s3 import S3Client

from src.app.user.schema.cloud import (
    PresignedDeleteRequest,
    PresignedGetRequest,
    PresignedHeader,
    PresignedPutRequest,
    PresignedResponse,
)
from src.core.config import settings
from src.core.dependencies.auth import get_current_user, get_current_user_without_error
from src.core.utils.frappeclient import AsyncFrappeClient

logger = logging.getLogger(__name__)


class CloudService:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
        s3_client: S3Client,
    ):
        self.frappe_client = frappe_client
        self.s3_client = s3_client

    def generate_sse_c_headers(self):
        raw_key = os.urandom(32)
        key = base64.b64encode(raw_key).decode("utf-8")
        md5 = base64.b64encode(hashlib.md5(raw_key).digest()).decode("utf-8")

        return {
            "SSECustomerAlgorithm": "AES256",
            "SSECustomerKey": key,
            "SSECustomerKeyMD5": md5,
        }

    def get_presigned_url(self, method: str, key: str, expires: int, headers: dict[str, str]):
        try:
            response = self.s3_client.generate_presigned_url(
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
        user: get_current_user_without_error,
        data: Annotated[PresignedPutRequest, Query()],
    ) -> PresignedResponse:
        key = f"{data.suffix}_{uuid4()}"
        headers = self.generate_sse_c_headers()
        presigned_url = self.get_presigned_url("put_object", key, 600, headers)

        response.headers["x-amz-server-side-encryption-customer-algorithm"] = headers.get("SSECustomerAlgorithm")
        response.headers["x-amz-server-side-encryption-customer-key"] = headers.get("SSECustomerKey")
        response.headers["x-amz-server-side-encryption-customer-key-md5"] = headers.get("SSECustomerKeyMD5")

        return PresignedResponse(
            presigned_url=presigned_url,
            algorithm="AES256",
            key=key,
            sse_key=headers.get("SSECustomerKey"),
            md5=headers.get("SSECustomerKeyMD5"),
        )

    async def create_get_presigned_url(
        self,
        data: Annotated[PresignedGetRequest, Query()],
        headers: Annotated[PresignedHeader, Header()],
    ) -> PresignedResponse:
        algorithm = data.algorithm or headers.x_amz_server_side_encryption_customer_algorithm
        key = data.sse_key or headers.x_amz_server_side_encryption_customer_key
        md5 = (
            data.md5
            or headers.x_amz_server_side_encryption_customer_key_MD5
            or base64.b64encode(hashlib.md5(base64.b64decode(key)).digest()).decode("utf-8")
        )

        if not algorithm or not key:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

        headers = {
            "SSECustomerAlgorithm": algorithm,
            "SSECustomerKey": key,
            "SSECustomerKeyMD5": md5,
        }

        presigned_url = self.get_presigned_url("get_object", data.key, 3600, headers)

        return PresignedResponse(
            presigned_url=presigned_url,
            algorithm=algorithm,
            key=data.key,
            sse_key=data.sse_key,
            md5=md5,
        )

    async def delete_file(
        self,
        user: get_current_user,
        data: Annotated[PresignedDeleteRequest, Query()],
    ) -> None:
        file = await self.frappe_client.get_doc("Files", data.key)
        if not file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        parent = file.get("parent")
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        sub = await self.frappe_client.get_value(
            "Project",
            "custom_sub",
            filters={"project_name": parent},
        )
        if sub.get("custom_sub") != user.sub:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        try:
            self.s3_client.delete_object(
                Bucket=settings.cloudflare.storage_bucket_name,
                Key=data.key,
            )
        except ClientError as e:
            logger.error("Cloudflare delete error: %s", e)
            raise HTTPException(status_code=500, detail="Deletion failed")

        await self.frappe_client.delete("Files", data.key)
