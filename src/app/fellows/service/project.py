from typing import Annotated

import openai
from fastapi import HTTPException, Path, Query
from sqlalchemy import cast, desc, func, select
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import selectinload

from src.app.fellows.data.project import estimation_instruction
from src.app.fellows.model.project import ProjectInfo
from src.app.fellows.repository.project import ProjectInfoRepository, ProjectRepository
from src.app.fellows.schema.project import GetProjectsRequest, ProjectInfoSchema, ProjectSchema
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        project_info_repository: ProjectInfoRepository,
        client: openai.AsyncOpenAI,
    ):
        self.project_repository = project_repository
        self.project_info_repository = project_info_repository
        self.client = client

    async def create_project(
        self,
        data: ProjectInfoSchema,
        user: get_current_user,
        session: postgres_session,
    ):
        project_info = ProjectInfo(**data.model_dump(exclude_unset=True))

        project = await self.project_repository.create(
            session,
            sub=user.sub,
            project_info=project_info,
        )

    async def get_project(
        self,
        user: get_current_user,
        session: postgres_session,
        project_id: str = Path(),
    ):
        result = await self.project_repository.get(
            session,
            [
                self.project_repository.model.project_id == project_id,
                self.project_repository.model.sub == user.sub,
            ],
            options=[selectinload(self.project_repository.model.project_info)],
            stmt=select(self.project_repository.model),
        )

        project = result.one_or_none()

        if project is None:
            raise HTTPException(status_code=404)

        return project[0]

    async def get_projects(
        self,
        data: Annotated[GetProjectsRequest, Query()],
        user: get_current_user,
        session: postgres_session,
    ):
        if not hasattr(self.project_repository.model, data.order_by):
            raise HTTPException(status_code=404, detail="Order Column name was Not found")

        filters = [self.project_repository.model.sub == user.sub]

        if data.keyword:
            tsv_name = func.to_tsvector("simple", self.project_info_repository.model.project_name)
            tsv_summary = func.to_tsvector("simple", self.project_info_repository.model.project_summary)
            tsv_concat = cast(tsv_name, TSVECTOR).op("||")(cast(tsv_summary, TSVECTOR))
            ts_query = func.websearch_to_tsquery("simple", data.keyword)
            filters.append(tsv_concat.op("@@")(ts_query))

        result = await self.project_repository.get_page(
            session,
            data.page,
            data.size,
            filters,
            orderby=[desc(getattr(self.project_repository.model, data.order_by))],
            options=[selectinload(self.project_repository.model.project_info)],
            join=[self.project_repository.model.project_info],
        )

        return result.scalars().all()

    async def update_project(
        self,
        data: ProjectInfoSchema,
        user: get_current_user,
        session: postgres_session,
        project_id: str = Path(),
    ):
        project_info = ProjectInfo(**data.model_dump(exclude_unset=True))

        result = await self.project_repository.update(
            session,
            [
                self.project_repository.model.project_id == project_id,
                self.project_repository.model.sub == user.sub,
            ],
            project_info=project_info,
        )

        return result

    async def get_project_estimate(
        self,
        user: get_current_user,
        session: postgres_session,
        project_id: str = Path(),
    ):
        result = None
        data = await self.get_project(user, session, project_id)
        project = ProjectSchema.model_validate(data)
        payload = project.project_info.model_dump_json()

        stream = await self.client.responses.create(
            model="ft:gpt-4.1-mini-2025-04-14:personal:fellows:BU1ht93V",
            instructions=estimation_instruction,
            input=payload,
            max_output_tokens=2000,
            temperature=0.0,
            top_p=0.02,
            stream=True,
        )

        async for event in stream:
            if event.type == "response.output_text.delta":
                for chunk in event.delta.splitlines():
                    yield f"data: {chunk}\n"
                if event.delta.endswith("\n"):
                    yield "data: \n"
                yield "\n"

            elif event.type == "response.output_text.done":
                yield "event: stream_done\n"  # 이벤트 타입 지정
                yield "data: \n\n"
            elif event.type == "response.completed":
                await self.project_repository.update(
                    session,
                    [
                        self.project_repository.model.project_id == project_id,
                        self.project_repository.model.sub == user.sub,
                    ],
                    ai_estimate=event.response.output_text,
                )
                break
