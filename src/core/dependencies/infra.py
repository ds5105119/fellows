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
