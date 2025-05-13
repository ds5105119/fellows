from sqlite3 import IntegrityError
from typing import Annotated

import openai
from fastapi import HTTPException, Path, Query, status
from sqlalchemy import asc, cast, desc, exists, func, select
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import subqueryload

from src.app.fellows.data.project import estimation_instruction, feature_estimate_instruction
from src.app.fellows.repository.project import ProjectInfoFileRecordRepository, ProjectInfoRepository, ProjectRepository
from src.app.fellows.schema.project import (
    GetProjectsRequest,
    ProjectFeatureEstimateRequest,
    ProjectFileRecordsSchema,
    ProjectInfoSchema,
    ProjectSchema,
)
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import postgres_session


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        project_info_repository: ProjectInfoRepository,
        project_info_file_record_repository: ProjectInfoFileRecordRepository,
        client: openai.AsyncOpenAI,
    ):
        self.project_repository = project_repository
        self.project_info_repository = project_info_repository
        self.project_info_file_record_repository = project_info_file_record_repository
        self.client = client

    def _keyword_to_project_filter(self, keyword: str):
        tsv_name = func.to_tsvector("simple", self.project_info_repository.model.project_name)
        tsv_summary = func.to_tsvector("simple", self.project_info_repository.model.project_summary)
        tsv_concat = cast(tsv_name, TSVECTOR).op("||")(cast(tsv_summary, TSVECTOR))
        ts_query = func.websearch_to_tsquery("simple", keyword)
        return tsv_concat.op("@@")(ts_query)

    async def create_project(
        self,
        data: ProjectInfoSchema,
        user: get_current_user,
        session: postgres_session,
    ):
        project_info_data = data.model_dump(exclude_unset=True, exclude={"files"})
        project_info = self.project_info_repository.model(**project_info_data)
        file_records: list[ProjectFileRecordsSchema] = data.files or []

        for file in file_records:
            project_info.files.append(
                self.project_info_file_record_repository.model(
                    file_record_key=file.file_record_key,
                )
            )

        project = await self.project_repository.create(
            session,
            sub=user.sub,
            project_info=project_info,
        )

        project = await self.get_project(user, session, project.project_id)

        return project

    async def get_project(
        self,
        user: get_current_user,
        session: postgres_session,
        project_id: str = Path(),
    ):
        result = await self.project_repository.get_instance(
            session,
            [
                self.project_repository.model.project_id == project_id,
                self.project_repository.model.sub == user.sub,
            ],
            options=[
                subqueryload(self.project_repository.model.project_info)
                .subqueryload(self.project_info_repository.model.files)
                .subqueryload(self.project_info_file_record_repository.model.file_record)
            ],
        )

        project = result.one_or_none()

        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return project[0]

    async def get_projects(
        self,
        data: Annotated[GetProjectsRequest, Query()],
        user: get_current_user,
        session: postgres_session,
    ):
        order_by_table, order_by, order_sort = self.project_repository.model, data.order_by, asc
        if data.order_by.find("project_info.") != -1:
            order_by_table, order_by = self.project_info_repository.model, ".".join(order_by.split(".")[1:])
        if order_by.split(".")[-1] == "desc":
            order_by, order_sort = ".".join(order_by.split(".")[:-1]), desc

        if not hasattr(order_by_table, order_by):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order Column name was Not found",
            )

        filters = [self.project_repository.model.sub == user.sub]

        if data.keyword:
            filters.append(self._keyword_to_project_filter(data.keyword))

        result = await self.project_repository.get_page_with_total(
            session,
            data.page,
            data.size,
            filters,
            orderby=[order_sort(getattr(order_by_table, order_by))],
            options=[
                subqueryload(self.project_repository.model.project_info)
                .subqueryload(self.project_info_repository.model.files)
                .subqueryload(self.project_info_file_record_repository.model.file_record)
            ],
            join=[
                self.project_info_repository.model,
                self.project_repository.model.project_info_id == self.project_info_repository.model.id,
            ],
        )

        if result.total:
            result.items = result.items.scalars().all()

        return result

    async def get_project_for_developer(
        self,
        user: get_current_user,
        session: postgres_session,
        project_id: str = Path(),
    ):
        dev_items = [item for item in user.groups if "/dev" in item]

        if not dev_items:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        result = await self.project_repository.get_instance(
            session,
            [
                self.project_repository.model.project_id == project_id,
                self.project_repository.model.status == "approved"
                or (
                    self.project_repository.model.status == "process"
                    and self.project_repository.model.groups.op("&&")(dev_items)
                ),
            ],
            options=[
                subqueryload(self.project_repository.model.project_info)
                .subqueryload(self.project_info_repository.model.files)
                .subqueryload(self.project_info_file_record_repository.model.file_record)
            ],
        )

        project = result.one_or_none()

        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        return project[0]

    async def get_projects_for_developer(
        self,
        data: Annotated[GetProjectsRequest, Query()],
        user: get_current_user,
        session: postgres_session,
    ):
        dev_items = [item for item in user.groups if "/dev" in item]

        if not dev_items:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        if not hasattr(self.project_repository.model, data.order_by):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order Column name was Not found",
            )

        filters = [
            self.project_repository.model.status == "approved"
            or (
                self.project_repository.model.status == "process"
                and self.project_repository.model.groups.op("&&")(dev_items)
            )
        ]

        if data.keyword:
            filters.append(self._keyword_to_project_filter(data.keyword))

        result = await self.project_repository.get_page(
            session,
            data.page,
            data.size,
            filters,
            orderby=[desc(getattr(self.project_repository.model, data.order_by))],
            options=[
                subqueryload(self.project_repository.model.project_info)
                .subqueryload(self.project_info_repository.model.files)
                .subqueryload(self.project_info_file_record_repository.model.file_record)
            ],
            join=[self.project_repository.model.project_info],
        )

        return result.scalars().all()

    async def update_project_info(
        self,
        data: ProjectInfoSchema,
        user: get_current_user,
        session: postgres_session,
        project_id: str = Path(),
    ):
        payload = data.model_dump(exclude_unset=True, exclude={"files"})

        subquery = select(self.project_repository.model.project_id).where(
            self.project_repository.model.project_id == project_id,
            self.project_repository.model.sub == user.sub,
            self.project_repository.model.project_info_id == self.project_info_repository.model.id,
        )

        result = await self.project_info_repository.update(
            session,
            filters=[
                exists(subquery),
            ],
            **payload,
        )

        return await self.get_project(user, session, project_id)

    async def add_file_to_project(
        self,
        data: ProjectFileRecordsSchema,
        user: get_current_user,
        session: postgres_session,
        project_id: str = Path(),
    ):
        project_info_result = await self.project_info_repository.get_instance(
            session,
            [
                self.project_repository.model.project_id == project_id,
                self.project_repository.model.sub == user.sub,
            ],
            options=[
                subqueryload(self.project_info_repository.model.files),
            ],
            join=[
                (
                    self.project_repository.model,
                    self.project_info_repository.model.project,
                ),
            ],
        )

        project_info = project_info_result.one_or_none()

        if project_info is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        project_info = project_info[0]

        try:
            await self.project_info_file_record_repository.create(
                session,
                project_info_id=project_info.id,
                file_record_key=data.file_record_key,
            )
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        return await self.get_project(user, session, project_id)

    async def delete_project(
        self,
        user: get_current_user,
        session: postgres_session,
        project_id: str = Path(),
    ):
        await self.project_repository.delete_by_project_id_sub(session, project_id, user.sub)

    async def get_project_feature_estimate(
        self,
        user: get_current_user,
        project_base: Annotated[ProjectFeatureEstimateRequest, Query()],
    ):
        payload = project_base.model_dump_json()

        response = await self.client.responses.create(
            model="gpt-4.1-mini-2025-04-14",
            instructions=feature_estimate_instruction,
            input=payload,
            max_output_tokens=1000,
            temperature=0.0,
            top_p=1.0,
        )

        result = [s.strip() for s in response.output_text.split(",")]

        return result

    async def get_project_estimate(
        self,
        user: get_current_user,
        session: postgres_session,
        project_id: str = Path(),
    ):
        data = await self.get_project(user, session, project_id)
        project = ProjectSchema.model_validate(data)
        payload = project.project_info.model_dump_json()

        stream = await self.client.responses.create(
            model="ft:gpt-4.1-mini-2025-04-14:personal:fellows:BU1ht93V",
            instructions=estimation_instruction,
            input=payload,
            max_output_tokens=2000,
            temperature=0.0,
            top_p=1.0,
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
