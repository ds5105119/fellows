import asyncio
import datetime
import random
import string

from fastapi import HTTPException

from src.app.fellows.schema.project import *
from src.app.fellows.schema.project import UserERPNextProject
from src.core.utils.frappeclient import AsyncFrappeClient


def generate_date_based_random_string(length=12):
    date_part = datetime.datetime.now().strftime("%Y")
    characters = string.ascii_lowercase + string.digits
    return date_part + "".join(random.choices(characters, k=length)).upper()


class FrappCreateRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client

    async def create_project(self, data: UserERPNextProject, sub: str):
        project = await self.frappe_client.insert(
            data.model_dump(by_alias=True)
            | {
                "doctype": "Project",
                "custom_sub": sub,
                "project_name": generate_date_based_random_string(),
                "custom_deletable": True,
                "custom_project_status": "draft",
                "project_type": "External",
                "company": "Fellows",
                "is_active": "No",
            }
        )

        return ERPNextProject(**project)

    async def create_task(self, data: ERPNextTask):
        task = await self.frappe_client.insert(data.model_dump(exclude_unset=True) | {"doctype": "Task"})
        return ERPNextTask(**task)

    async def create_todo_many(self, data: list[ERPNextToDo]):
        await self.frappe_client.insert_many([d.model_dump(exclude_unset=True) | {"doctype": "ToDo"} for d in data])

    async def create_file(self, data: ERPNextFile):
        file = await self.frappe_client.insert(data.model_dump(exclude_unset=True) | {"doctype": "Files"})
        return ERPNextFile(**file)


class FrappReadRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client

    async def get_project_by_id(self, project_id: str, sub: str):
        project = await self.frappe_client.get_doc("Project", project_id, filters={"custom_sub": sub})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return ERPNextProject(**project)

    async def get_projects(
        self,
        data: ERPNextProjectsRequest,
        sub: str,
    ):
        filters = {"custom_sub": sub}

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

        projects = await self.frappe_client.get_list(
            "Project",
            filters=filters,
            limit_start=data.page * data.size,
            limit_page_length=data.size,
            order_by=order_by,
        )

        return ProjectsPaginatedResponse.model_validate({"items": projects}, from_attributes=True)

    async def get_task(self, project_id: str, subject: str):
        data = await self.frappe_client.get_doc("Task", subject, filters={"project": project_id})
        return ERPNextTask(**data)

    async def get_tasks(self, user_sub: str, data: ERPNextTasksRequest):
        filters = {"custom_sub": user_sub, "custom_is_user_visible": True}
        or_filters = {}

        if data.start:
            filters["exp_start_date"] = [">=", data.start]
        if data.end:
            filters["exp_end_date"] = ["<=", data.end]

        if type(data.status) == str:
            filters["custom_project_status"] = ["like", data.status]
        elif type(data.status) == list:
            or_filters["custom_project_status"] = ["like", data.status[0]]

        order_by = None

        if type(data.order_by) == str:
            order_by = data.order_by
        elif type(data.order_by) == list:
            order_by = [f"{o.split('.')[0]} desc" if o.split(".")[-1] == "desc" else o for o in data.order_by]

        tasks = await self.frappe_client.get_list(
            "Task",
            filters=filters,
            or_filters=or_filters,
            limit_start=data.page * data.size,
            limit_page_length=data.size,
            order_by=order_by,
        )

        return ERPNextTaskPaginatedResponse.model_validate({"items": tasks}, from_attributes=True)

    async def get_file(self, project_id: str, key: str, task_id: str | None = None) -> ERPNextFile:
        filters = {"project": project_id}
        if task_id:
            filters["task"] = task_id

        data = await self.frappe_client.get_doc("Files", key, filters)
        return ERPNextFile(**data)

    async def get_files(self, project_id: str, data: ERPNextFileRequest):
        filters = {"project": project_id}

        if data.task:
            filters["task"] = data.task
        if data.issue:
            filters["issue"] = data.issue

        order_by = None

        if data.order_by:
            if data.order_by.split(".")[-1] == "desc":
                order_by = f"{data.order_by.split('.')[0]} desc"
            else:
                order_by = data.order_by

        files = await self.frappe_client.get_list(
            "Files",
            filters=filters,
            limit_start=data.page * data.size,
            limit_page_length=data.size,
            order_by=order_by,
        )

        return ERPNextFilesResponse.model_validate({"items": files}, from_attributes=True)


class FrappUpdateRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client

    async def update_project_by_id(
        self,
        project_id: str,
        data: UpdateERPNextProject,
    ):
        project = await self.frappe_client.update(
            {
                "doctype": "Project",
                "name": project_id,
                **data.model_dump(exclude={"custom_files"}, by_alias=True, exclude_unset=True),
            }
        )

        return ERPNextProject(**project)


class FrappDeleteRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client

    async def delete_project_by_id(self, project_id: str):
        tasks = await self.frappe_client.get_list("Task", fields=["name"], filters={"project": project_id})
        issues = await self.frappe_client.get_list("Issue", fields=["name"], filters={"project": project_id})
        files = await self.frappe_client.get_list("Files", fields=["name"], filters={"project": project_id})

        await asyncio.gather(
            *[self.frappe_client.delete("Task", task["name"]) for task in tasks],
            *[self.frappe_client.delete("Issue", issue["name"]) for issue in issues],
            *[self.frappe_client.delete("Files", file["name"]) for file in files],
        )

        await self.frappe_client.delete("Project", project_id)

    async def delete_task_by_id(self, task_id: str):
        await self.frappe_client.delete("Task", task_id)

    async def delete_file(self, key: str):
        await self.frappe_client.delete("Files", key)


class FrappeRepository(
    FrappCreateRepository,
    FrappReadRepository,
    FrappUpdateRepository,
    FrappDeleteRepository,
):
    pass
