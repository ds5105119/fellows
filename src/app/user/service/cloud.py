import base64
import hashlib
import logging
import os
from typing import Annotated
from urllib.parse import urlparse
from uuid import uuid4

from botocore.client import ClientError
from fastapi import Header, HTTPException, Query, Request, Response, status
from mypy_boto3_s3 import S3Client

from src.app.user.schema.cloud import *
from src.core.config import settings
from src.core.dependencies.auth import get_current_user
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

    def get_presigned_url(self, method: str, key: str, expires: int, headers: dict[str, str] | None = None):
        if headers is None:
            headers = {}

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
        user: get_current_user,
        data: Annotated[PresignedPutRequest, Query()],
    ) -> PresignedPutResponse:
        key = f"/{data.suffix}/{user.sub}/{data.name}_{uuid4()}"
        presigned_url = self.get_presigned_url("put_object", key, 600)

        return PresignedPutResponse(key=key, presigned_url=presigned_url)

    async def create_put_presigned_url_for_fellows(
        self,
        request: Request,
        data: Annotated[PresignedPutRequest, Query()],
    ) -> PresignedPutResponse:
        allowed_domains = settings.allowed_hosts

        def extract_domain(url: str) -> str:
            try:
                return urlparse(url).hostname or ""
            except:
                return ""

        origin = request.headers.get("origin", "")
        referer = request.headers.get("referer", "")
        host = request.headers.get("host", "")

        origin_host = extract_domain(origin)
        referer_host = extract_domain(referer)
        host_clean = host.split(":")[0]

        if (
            origin_host not in allowed_domains
            and referer_host not in allowed_domains
            and host_clean not in allowed_domains
        ):
            raise HTTPException(status_code=403, detail="Unauthorized domain")

        key = f"/fellows/{data.suffix}/{data.name}_{uuid4()}"
        presigned_url = self.get_presigned_url("put_object", key, 600)

        return PresignedPutResponse(key=key, presigned_url=presigned_url)

    async def create_sse_c_put_presigned_url(
        self,
        response: Response,
        user: get_current_user,
        data: Annotated[PresignedPutRequest, Query()],
    ) -> SSECPresignedResponse:
        key = f"/{data.suffix}/{user.sub}/{data.name}_{uuid4()}"
        headers = self.generate_sse_c_headers()
        presigned_url = self.get_presigned_url("put_object", key, 600, headers)

        response.headers["x-amz-server-side-encryption-customer-algorithm"] = headers.get("SSECustomerAlgorithm")
        response.headers["x-amz-server-side-encryption-customer-key"] = headers.get("SSECustomerKey")
        response.headers["x-amz-server-side-encryption-customer-key-md5"] = headers.get("SSECustomerKeyMD5")

        return SSECPresignedResponse(
            presigned_url=presigned_url,
            algorithm="AES256",
            key=key,
            sse_key=headers.get("SSECustomerKey"),
            md5=headers.get("SSECustomerKeyMD5"),
        )

    async def create_sse_c_put_presigned_url_for_fellows(
        self,
        response: Response,
        request: Request,
        data: Annotated[PresignedPutRequest, Query()],
    ) -> SSECPresignedResponse:
        allowed_domains = settings.allowed_hosts

        def extract_domain(url: str) -> str:
            try:
                return urlparse(url).hostname or ""
            except:
                return ""

        origin = request.headers.get("origin", "")
        referer = request.headers.get("referer", "")
        host = request.headers.get("host", "")

        origin_host = extract_domain(origin)
        referer_host = extract_domain(referer)
        host_clean = host.split(":")[0]

        if (
            origin_host not in allowed_domains
            and referer_host not in allowed_domains
            and host_clean not in allowed_domains
        ):
            raise HTTPException(status_code=403, detail="Unauthorized domain")

        key = f"/fellows/{data.suffix}/{data.name}_{uuid4()}"
        headers = self.generate_sse_c_headers()
        presigned_url = self.get_presigned_url("put_object", key, 600, headers)

        response.headers["x-amz-server-side-encryption-customer-algorithm"] = headers.get("SSECustomerAlgorithm")
        response.headers["x-amz-server-side-encryption-customer-key"] = headers.get("SSECustomerKey")
        response.headers["x-amz-server-side-encryption-customer-key-md5"] = headers.get("SSECustomerKeyMD5")

        return SSECPresignedResponse(
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
    ) -> str:
        presigned_url = self.get_presigned_url("get_object", data.key, 600)

        return presigned_url

    async def create_sse_c_get_presigned_url(
        self,
        data: Annotated[PresignedSSECGetRequest, Query()],
        headers: Annotated[PresignedHeader, Header()],
    ) -> SSECPresignedResponse:
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

        return SSECPresignedResponse(
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

        project = file.get("project")
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        sub = await self.frappe_client.get_value(
            "Project",
            "custom_sub",
            filters={"project_name": project},
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
