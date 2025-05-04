from typing import Annotated, AsyncIterable

from fastapi import APIRouter, Query
from starlette.responses import StreamingResponse
from webtool.throttle import limiter

from src.app.fellows.api.dependencies import ai_service
from src.app.fellows.schema.ai import ProjectEstimateRequest

router = APIRouter()


@limiter(max_requests=300)
@router.get("/estimate", response_class=StreamingResponse)
async def estimate_stream(
    request: Annotated[ProjectEstimateRequest, Query()],
):
    async def event_generator() -> AsyncIterable[str]:
        async for chunk in ai_service.project_estimate(request):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
