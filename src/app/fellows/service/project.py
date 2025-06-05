import asyncio
from datetime import date, timedelta
from logging import getLogger
from typing import Annotated
from uuid import uuid4

import openai
from fastapi import HTTPException, Path, Query, status

from src.app.fellows.data.project import *
from src.app.fellows.schema.project import *
from src.core.dependencies.auth import get_current_user
from src.core.utils.frappeclient import AsyncFrappeClient

logger = getLogger(__name__)


class ProjectService:
    def __init__(
        self,
        openai_client: openai.AsyncOpenAI,
        frappe_client: AsyncFrappeClient,
    ):
        self.openai_client = openai_client
        self.frappe_client = frappe_client

    async def create_project(
        self,
        data: UserERPNextProject,
        user: get_current_user,
    ) -> ERPNextProject:
        payload = data.model_dump(by_alias=True) | {
            "doctype": "Project",
            "custom_sub": user.sub,
            "project_name": str(uuid4()),
            "custom_deletable": True,
            "custom_project_status": "draft",
            "project_type": "External",
            "company": "Fellows",
            "is_active": "No",
        }

        project = await self.frappe_client.insert(payload)

        return ERPNextProject(**project)

    async def get_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ) -> ERPNextProject:
        project = await self.frappe_client.get_doc("Project", project_id, filters={"custom_sub": user.sub})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        print(project)

        return ERPNextProject(**project)

    async def get_projects(
        self,
        data: Annotated[ERPNextProjectsRequest, Query()],
        user: get_current_user,
    ) -> ProjectsPaginatedResponse:
        filters = {"custom_sub": user.sub}
        if data.status:
            filters["custom_project_status"] = ["like", f"%{data.status}%"]
        if data.keyword:
            filters["custom_project_title"] = ["like", f"%{data.keyword}%"]

        order_by = None
        if data.order_by:
            if data.order_by.split(".")[-1] == "desc":
                order_by = f"{data.order_by.split('.')[0]} desc"
            else:
                order_by = data.order_by

        result = await self.frappe_client.get_list(
            "Project",
            filters=filters,
            limit_start=data.page * data.size,
            limit_page_length=data.size,
            order_by=order_by,
        )
        return ProjectsPaginatedResponse.model_validate({"items": result}, from_attributes=True)

    async def update_project_info(
        self,
        data: UserERPNextProject,
        user: get_current_user,
        project_id: str = Path(),
    ) -> ERPNextProject:
        project = await self.get_project(user, project_id)

        updated_project = await self.frappe_client.update(
            {
                "doctype": "Project",
                "name": project.project_name,
                **data.model_dump(exclude={"custom_files"}, by_alias=True),
            }
        )

        return ERPNextProject(**updated_project)

    async def add_files(
        self,
        user: get_current_user,
        data: ERPNextProjectFileRow,
        project_id: str = Path(),
    ):
        project = await self.get_project(user, project_id)
        project_dict = project.model_dump(include={"custom_files"})

        custom_files = project_dict.get("custom_files", [])
        custom_files.append(
            {
                "doctype": "Files",
                "algorithm": data.algorithm,
                "file_name": data.file_name,
                "key": data.key,
                "sse_key": data.sse_key,
                "uploader": data.uploader,
            }
        )

        await self.frappe_client.update(
            {
                "doctype": "Project",
                "name": project.project_name,
                "custom_files": custom_files,
            }
        )

    async def delete_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ):
        project = await self.get_project(user, project_id)
        if not project.custom_deletable:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        tasks = await self.frappe_client.get_list("Task", fields=["name"], filters={"project": project_id})
        await asyncio.gather(*[self.frappe_client.delete("Task", task["name"]) for task in tasks])

        await self.frappe_client.delete("Project", project_id)

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

        project = await self.get_project(user, project_id)

        if project.custom_project_status != "draft":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        managers = await self.frappe_client.get_doc("User Group", "Managers")

        updated_project = await self.frappe_client.update(
            {
                "doctype": "Project",
                "name": project.project_name,
                "custom_project_status": "process:1",
                "is_active": "Yes",
            }
        )

        erp_next_task = ERPNextTask(
            doctype="Task",
            subject="Initial Planning and Vendor Quotation Review",
            project=project_id,
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

        task = await self.frappe_client.insert(erp_next_task.model_dump(exclude_unset=True))

        erp_next_todos = [
            ERPNextToDo(
                doctype="ToDo",
                priority=ERPNextToDoPriority.HIGH,
                color="#FF4500",
                allocated_to=manager["user"],
                description=f"Allocated Initial Planning and Vendor Quotation Review Task for {project_id}",
                reference_type="Task",
                reference_name=task.get("name"),
            ).model_dump(exclude_unset=True)
            for manager in managers["user_group_members"]
        ]

        await self.frappe_client.insert_many(erp_next_todos)

    async def cancel_submit_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ):
        project = await self.get_project(user, project_id)

        if project.custom_project_status != "process:1":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        updated_project = await self.frappe_client.update(
            {
                "doctype": "Project",
                "name": project.project_name,
                "custom_project_status": "draft",
                "is_active": "No",
            }
        )

        tasks = await self.frappe_client.get_list("Task", fields=["name"], filters={"project": project_id})
        await asyncio.gather(*[self.frappe_client.delete("Task", task["name"]) for task in tasks])

    async def get_project_tasks(
        self,
        user: get_current_user,
        data: Annotated[ProjectTaskRequest, Query()],
        project_id: str = Path(),
    ):
        project = await self.get_project(user, project_id)

        if user.sub != project.custom_sub:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        tasks = await self.frappe_client.get_list(
            "Task",
            fields=[
                "subject",
                "project",
                "color",
                "status",
                "exp_start_date",
                "expected_time",
                "exp_end_date",
                "progress",
                "description",
                "closing_date",
            ],
            filters={"project": project_id, "custom_is_user_visible": True},
            limit_start=data.page,
            limit_page_length=data.size,
        )

        return ERPNextTaskPaginatedResponse(items=tasks)

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
        project = await self.get_project(user, project_id)

        if project.custom_project_status != "draft":
            return

        payload = project.model_dump_json(
            include={
                "custom_project_title",
                "custom_project_summary",
                "custom_readiness_level",
                "expected_start_date",
                "custom_design_requirements",
                "custom_content_pages",
                "custom_maintenance_required",
                "custom_platforms",
                "custom_features",
                "custom_preferred_tech_stacks",
            }
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
