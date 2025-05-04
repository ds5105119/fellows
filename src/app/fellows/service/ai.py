import openai

from src.app.fellows.data.ai import estimation_instruction
from src.app.fellows.schema.ai import ProjectEstimateRequest


class AIService:
    def __init__(self, client: openai.AsyncOpenAI):
        self.client = client

    async def project_estimate(
        self,
        data: ProjectEstimateRequest,
    ):
        payload = data.model_dump_json()
        stream = await self.client.responses.create(
            model="gpt-4.1-mini",
            instructions=estimation_instruction,
            input=payload,
            max_output_tokens=1000,
            temperature=0.0,
            stream=True,
        )

        async for event in stream:
            if event.type == "response.output_text.delta":
                for chunk in event.delta.splitlines():
                    yield f"data: {chunk}\r\n"
                if event.delta.endswith("\n"):
                    yield "data: \r\n"
                yield "\r\n"
            elif event.type == "response.output_text.done":
                yield "data: \r\n\r\n"
            elif event.type == "response.completed":
                break
