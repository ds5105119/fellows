import openai

from src.app.fellows.service.ai import AIService
from src.core.config import settings

client = openai.AsyncOpenAI(api_key=settings.openai_api.key)
ai_service = AIService(client)
