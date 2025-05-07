import openai
from nats import NATS

from src.core.config import settings

nc = NATS()
client = openai.AsyncOpenAI(api_key=settings.openai_api.key)
