import boto3
import openai
from nats import NATS

from src.core.config import settings
from src.core.utils.frappeclient import AsyncFrappeClient

nc = NATS()

openai_client = openai.AsyncOpenAI(api_key=settings.openai_api.key)

frappe_client = AsyncFrappeClient(
    url=settings.frappe_api.url,
    api_key=settings.frappe_api.key,
    api_secret=settings.frappe_api.secret,
)

r2 = boto3.client(
    service_name="s3",
    endpoint_url=f"https://{settings.cloudflare.account_id}.r2.cloudflarestorage.com",
    aws_access_key_id=settings.cloudflare.access_key_id,
    aws_secret_access_key=settings.cloudflare.secret_access_key,
    region_name="auto",
)

ses = boto3.client(
    "sesv2",
    aws_access_key_id=settings.aws.access_key_id,
    aws_secret_access_key=settings.aws.secret_access_key,
    aws_account_id=settings.aws.account_id,
    region_name="auto",
)
