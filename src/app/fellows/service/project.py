import asyncio
import json
from datetime import date, timedelta
from logging import getLogger
from typing import Annotated

import openai
from fastapi import HTTPException, Path, Query, status

from src.app.fellows.data.project import *
from src.app.fellows.repository.frappe import FrappeRepository
from src.app.fellows.schema.project import *
from src.app.user.schema.user_data import UpdateUserAttributes
from src.core.dependencies.auth import get_current_user
from src.core.utils.frappeclient import AsyncFrappeClient

logger = getLogger(__name__)


class ProjectService:
    def __init__(
        self,
        openai_client: openai.AsyncOpenAI,
        frappe_client: AsyncFrappeClient,
        frappe_repository: FrappeRepository,
    ):
        self.openai_client = openai_client
        self.frappe_client = frappe_client
        self.frappe_repository = frappe_repository

    async def create_project(
        self,
        data: UserERPNextProject,
        user: get_current_user,
    ) -> ERPNextProject:
        return await self.frappe_repository.create_project(data, user.sub)

    async def get_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ) -> ERPNextProject:
        return await self.frappe_repository.get_project_by_id(project_id, user.sub)

    async def get_projects(
        self,
        data: Annotated[ERPNextProjectsRequest, Query()],
        user: get_current_user,
    ) -> ProjectsPaginatedResponse:
        return await self.frappe_repository.get_projects(data, user.sub)

    async def update_project_info(
        self,
        data: UpdateUserAttributes,
        user: get_current_user,
        project_id: str = Path(),
    ) -> ERPNextProject:
        await self.frappe_repository.get_project_by_id(project_id, user.sub)
        return await self.frappe_repository.update_project_by_id(project_id, data)

    async def delete_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ):
        project = await self.frappe_repository.get_project_by_id(project_id, user.sub)
        print(project)
        if not project.custom_deletable:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        return await self.frappe_repository.delete_project_by_id(project.project_name)

    async def submit_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ) -> None:
        result = await self.frappe_client.get_list(
            "Project",
            fields=["project_name"],
            filters={"custom_sub": user.sub, "custom_project_status": ["like", "%process%"]},
        )

        if len(result) >= 15:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

        project = await self.frappe_repository.get_project_by_id(project_id, user.sub)
        managers = await self.frappe_client.get_doc("User Group", "Managers")

        if project.custom_project_status != "draft":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        await self.frappe_repository.update_project_by_id(
            project_id,
            UpdateERPNextProject(
                custom_project_status=CustomProjectStatus.PROCESS_1,
                is_active=IsActive.YES,
            ),
        )

        task = await self.frappe_repository.create_task(
            ERPNextTask(
                subject="Initial Planning and Vendor Quotation Review",
                project=project_id,
                custom_sub=user.sub,
                color="#FF4500",
                is_group=False,
                is_template=False,
                custom_is_user_visible=True,
                status="Open",
                priority="High",
                task_weight=1.0,
                exp_start_date=date.today(),
                exp_end_date=date.today() + timedelta(days=1),
                expected_time=4.0,
                duration=3,
                is_milestone=True,
                description="프로젝트 요구사항 분석 및 견적 내부 검토 후 실제 견적가를 알려드릴께요.",
                department="Management",
                company="Fellows",
            )
        )

        await self.frappe_repository.create_todo_many(
            [
                ERPNextToDo(
                    priority=ERPNextToDoPriority.HIGH,
                    color="#FF4500",
                    allocated_to=manager["user"],
                    description=f"Allocated Initial Planning and Vendor Quotation Review Task for {project_id}",
                    reference_type="Task",
                    reference_name=task.get("name"),
                ).model_dump(exclude_unset=True)
                for manager in managers["user_group_members"]
            ]
        )

    async def cancel_submit_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ):
        project = await self.frappe_repository.get_project_by_id(project_id, user.sub)

        if project.custom_project_status != "process:1":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await self.frappe_repository.update_project_by_id(
            project_id,
            UpdateERPNextProject(
                custom_project_status=CustomProjectStatus.DRAFT,
                is_active=IsActive.NO,
            ),
        )

        tasks = await self.frappe_repository.get_tasks(project.project_name)
        await asyncio.gather(*[self.frappe_repository.delete_task_by_id(task.name) for task in tasks.items])

    async def create_file(
        self,
        user: get_current_user,
        data: ERPNextFile,
        project_id: str = Path(),
    ) -> ERPNextFile:
        project = await self.frappe_repository.get_project_by_id(project_id, user.sub)
        payload = ERPNextFile(**data.model_dump(exclude={"project"}), project=project.project_name)
        return await self.frappe_repository.create_file(payload)

    async def read_file(
        self,
        user: get_current_user,
        project_id: str = Path(),
        key: str = Path(),
    ) -> ERPNextFile:
        project = await self.frappe_repository.get_project_by_id(project_id, user.sub)
        return await self.frappe_repository.get_file(project.project_name, key)

    async def read_files(
        self,
        user: get_current_user,
        data: Annotated[ERPNextFileRequest, Query()],
        project_id: str = Path(),
    ) -> ERPNextFilesResponse:
        project = await self.frappe_repository.get_project_by_id(project_id, user.sub)
        return await self.frappe_repository.get_files(project.project_name, data)

    async def delete_file(
        self,
        user: get_current_user,
        project_id: str = Path(),
        key: str = Path(),
    ):
        await self.frappe_repository.get_project_by_id(project_id, user.sub)
        await self.frappe_repository.delete_file(key)

    async def read_tasks(
        self,
        user: get_current_user,
        data: Annotated[ProjectTaskRequest, Query()],
        project_id: str = Path(),
    ) -> ERPNextTaskPaginatedResponse:
        project = await self.frappe_repository.get_project_by_id(project_id, user.sub)
        return await self.frappe_repository.get_tasks(project.project_name, data)

    async def get_project_feature_estimate(
        self,
        user: get_current_user,
        project_base: Annotated[ProjectFeatureEstimateRequest, Query()],
    ):
        payload = project_base.model_dump_json()

        response = await self.openai_client.responses.create(
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
        project_id: str = Path(),
    ):
        project = await self.frappe_repository.get_project_by_id(project_id, user.sub)
        project_dict = project.model_dump(exclude_unset=True)

        if project.custom_project_status != "draft" and project.custom_project_status != "process:1":
            return

        payload = json.dumps(
            {
                "project_name": project_dict.get("custom_project_title"),
                "project_summary": project_dict.get("custom_project_summary"),
                "platforms": project_dict.get("custom_platforms"),
                "readiness_level": project_dict.get("custom_readiness_level"),
                "start_date": project_dict.get("expected_start_date"),
                "desired_deadline": project_dict.get("expected_end_date"),
                "maintenance_required": project_dict.get("custom_maintenance_required"),
                "content_pages": project_dict.get("custom_content_pages"),
                "features": project_dict.get("custom_features"),
            },
            default=str,
        )

        stream = await self.openai_client.responses.create(
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
                ai_estimate = event.response.output_text
                try:
                    emoji, total_amount = await self.project_estimate_after_job(ai_estimate)
                except:
                    emoji, total_amount = None, None

                await self.frappe_client.update(
                    {
                        "doctype": "Project",
                        "name": project.project_name,
                        "custom_ai_estimate": ai_estimate,
                        "custom_emoji": emoji,
                        "estimated_costing": total_amount,
                    }
                )
                break

    async def project_estimate_after_job(self, ai_estimate: str):
        response = await self.openai_client.responses.create(
            model="gpt-4.1-mini-2025-04-14",
            instructions=project_information_instruction,
            input=ai_estimate,
            max_output_tokens=100,
            temperature=0.0,
            top_p=1.0,
        )

        result = [s.strip() for s in response.output_text.split(",")]

        emoji = result[0]
        total_amount = int(result[1])

        return emoji, total_amount
