import asyncio
import datetime
import json
import math
import random
import string
from datetime import timedelta

from fastapi import HTTPException

from src.app.fellows.schema.project import *
from src.core.dependencies.auth import get_current_user, keycloak_admin
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

    async def create_project(self, data: CreateERPNextProject, sub: str):
        project = await self.frappe_client.insert(
            data.model_dump(by_alias=True)
            | {
                "doctype": "Project",
                "project_name": generate_date_based_random_string(),
                "custom_deletable": True,
                "custom_project_status": "draft",
                "project_type": "External",
                "company": "Fellows",
                "is_active": "No",
                "customer": sub,
                "custom_team": json.dumps([{"member": sub, "level": 0}]),
            }
        )

        return ERPNextProjectForUser(**project)

    async def create_task(self, data: ERPNextTask, sub: str):
        task = await self.frappe_client.insert(
            data.model_dump(exclude_unset=True) | {"doctype": "Task", "customer": sub}
        )
        return ERPNextTask(**task)

    async def create_issue(self, data: CreateERPNextIssue, sub: str):
        issue = await self.frappe_client.insert(
            data.model_dump(exclude_unset=True) | {"doctype": "Issue", "customer": sub}
        )
        return ERPNextIssue(**issue)

    async def create_todo_many(self, data: list[ERPNextToDo]):
        await self.frappe_client.insert_many([d.model_dump(exclude_unset=True) | {"doctype": "ToDo"} for d in data])

    async def create_file(self, data: ERPNextFile):
        file = await self.frappe_client.insert(data.model_dump(exclude_unset=True) | {"doctype": "Files"})
        return ERPNextFile(**file)

    async def get_or_create_customer(self, user: get_current_user):
        customer = await self.frappe_client.get_doc("Customer", user.sub)
        if not customer:
            await self.frappe_client.insert(
                {
                    "doctype": "Customer",
                    "customer_name": user.sub,
                    "custom_username": user.name,
                    "customer_type": "Company",
                    "mobile_no": user.phone,
                    "email_id": user.email,
                }
            )

    async def create_report(
        self,
        project_id: str,
        start_date: datetime.date | str,
        end_date: datetime.date | str,
        summary: str,
    ):
        report = await self.frappe_client.insert(
            {
                "doctype": "Project Report",
                "project": project_id,
                "start_date": start_date,
                "end_date": end_date,
                "summary": summary,
            }
        )

        return ERPNextReport.model_validate(report)


class FrappReadRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client

    async def get_project_names(self, sub: str) -> list[dict]:
        # 1. 사용자가 접근 가능한 프로젝트 목록을 먼저 조회 (레벨 4 제외)
        all_member_projects = await self.frappe_client.get_list(
            "Project",
            fields=["project_name", "custom_team"],
            filters={"custom_team": ["like", f"%{sub}%"]},
        )

        accessible_projects = []
        for p in all_member_projects:
            team_members = json.loads(p.get("custom_team") or "[]")
            user_level = next((member["level"] for member in team_members if member["member"] == sub), 5)
            if user_level < 4:
                p["custom_team"] = team_members
                accessible_projects.append(p)

        return accessible_projects

    async def get_user_project_permission(self, project_id: str, sub: str) -> tuple[ERPNextProjectForUser, int]:
        """
        프로젝트 정보를 가져오고 사용자의 권한 레벨을 반환합니다.
        사용자가 프로젝트 멤버가 아니면 404 에러를 발생시킵니다.
        """
        project_doc = await self.frappe_client.get_doc("Project", project_id)
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")

        project = ERPNextProjectForUser(**project_doc)

        member_info = next((member for member in project.custom_team if member.member == sub), None)

        if not member_info:
            raise HTTPException(status_code=404, detail="Project not found or you are not a member.")

        return project, member_info.level

    async def get_project_by_id(self, project_id: str, sub: str):
        project, level = await self.get_user_project_permission(project_id, sub)
        if level > 4:
            raise HTTPException(status_code=401, detail="You do not have permission to access this project.")
        return project

    async def get_projects(
        self,
        data: ERPNextProjectsRequest,
        sub: str,
    ):
        filters = {}
        # 레벨 4인 사용자는 프로젝트 목록에서 제외되어야 하므로, like 검색은 유효
        or_filters = {"customer": sub, "custom_team": ["like", f"%{sub}%"]}

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
            or_filters=or_filters,
            limit_start=data.page * data.size,
            limit_page_length=data.size,
            order_by=order_by,
        )

        # 레벨 4 사용자의 프로젝트는 필터링
        accessible_projects = []
        for p in projects:
            team_members = json.loads(p.get("custom_team") or "[]")
            user_level = next((member["level"] for member in team_members if member["member"] == sub), 5)
            if user_level < 4:
                accessible_projects.append(p)

        return ProjectsPaginatedResponse.model_validate({"items": accessible_projects}, from_attributes=True)

    async def get_projects_overview(self, sub: str):
        projects = await self.frappe_client.get_list(
            "Project",
            fields=[
                "project_name",
                "custom_project_title",
                "custom_project_status",
                "custom_team",
                "creation",
                "modified",
                "expected_start_date",
                "expected_end_date",
                "custom_team",
            ],
            filters={"custom_team": ["like", f"%{sub}%"]},
        )

        # 레벨 4 사용자의 프로젝트는 필터링
        accessible_projects = []
        for p in projects:
            team_members = json.loads(p.get("custom_team") or "[]")
            user_level = next((member["level"] for member in team_members if member["member"] == sub), 5)
            if user_level < 4:
                p["custom_team"] = team_members
                accessible_projects.append(p)

        return OverviewProjectsPaginatedResponse.model_validate({"items": accessible_projects}, from_attributes=True)

    async def get_task(self, name: str):
        data = await self.frappe_client.get_doc("Task", name)
        if not data:
            raise HTTPException(status_code=404, detail="Task not found")
        return ERPNextTask(**data)

    async def get_tasks(
        self,
        page: int,
        size: int,
        sub: str,
        project_id: list[str] | str | None = None,
        order_by: list[str] | str | None = None,
        status: list[ERPNextTaskStatus] | ERPNextTaskStatus | None = None,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
        keyword: str | None = None,
    ):
        accessible_projects = await self.get_project_names(sub)

        if not accessible_projects:
            return ERPNextTaskPaginatedResponse(items=[])

        accessible_projects_names = [p["project_name"] for p in accessible_projects]

        filters = {"project": ["in", accessible_projects_names], "custom_is_user_visible": True}
        or_filters = {}

        if keyword:
            filters["subject"] = ["like", f"%{keyword}%"]
        if start:
            filters["exp_end_date"] = [">", start - timedelta(days=1)]
        if end:
            filters["exp_start_date"] = ["<", end + timedelta(days=1)]
        if isinstance(status, str):
            filters["status"] = ["like", status]
        elif isinstance(status, list):
            filters["status"] = ["in", status]
        if isinstance(project_id, str):
            filters["project"] = ["=", project_id]
        elif isinstance(project_id, list):
            filters["project"] = ["in", project_id]

        _order_by = None
        if isinstance(order_by, str):
            _order_by = order_by
        elif isinstance(order_by, list):
            _order_by = [f"{o.split('.')[0]} desc" if o.split(".")[-1] == "desc" else o for o in order_by]

        tasks = await self.frappe_client.get_list(
            "Task",
            filters=filters,
            or_filters=or_filters,
            limit_start=page * size,
            limit_page_length=size,
            order_by=_order_by,
        )

        return ERPNextTaskPaginatedResponse.model_validate({"items": tasks}, from_attributes=True)

    async def get_issue(self, name: str):
        data = await self.frappe_client.get_doc("Issue", name)
        if not data:
            raise HTTPException(status_code=404, detail="Issue not found")
        return ERPNextIssue(**data)

    async def get_issues(self, data: ERPNextIssuesRequest, sub: str):
        accessible_projects = await self.get_project_names(sub)

        if not accessible_projects:
            return ERPNextTaskPaginatedResponse(items=[])

        # filters를 딕셔너리가 아닌 리스트로 시작합니다.
        filters = []

        # project 필터 처리: data.project_id가 있으면 그것을 우선 사용하고, 없으면 접근 가능한 전체 프로젝트를 사용합니다.
        if data.project_id:
            if isinstance(data.project_id, str):
                filters.append(["Issue", "project", "=", data.project_id])
            elif isinstance(data.project_id, list):
                filters.append(["Issue", "project", "in", data.project_id])
        else:
            accessible_projects_names = [p["project_name"] for p in accessible_projects]
            filters.append(["Issue", "project", "in", accessible_projects_names])

        # 나머지 필터들을 리스트에 추가합니다.
        if data.keyword:
            filters.append(["Issue", "subject", "like", f"%{data.keyword}%"])

        # start와 end 날짜 필터를 각각 독립적으로 추가합니다.
        if data.start:
            filters.append(["Issue", "creation", ">", data.start - timedelta(days=1)])
        if data.end:
            filters.append(["Issue", "creation", "<", data.end + timedelta(days=1)])

        if isinstance(data.issue_type, str):
            filters.append(["Issue", "issue_type", "like", data.issue_type])
        elif isinstance(data.issue_type, list):
            # 이전 코드에 있던 버그 수정: issue_type인데 status를 필터링하는 문제를 바로잡았습니다.
            filters.append(["Issue", "issue_type", "in", data.issue_type])

        if isinstance(data.status, str):
            filters.append(["Issue", "status", "=", data.status])
        elif isinstance(data.status, list):
            filters.append(["Issue", "status", "in", data.status])

        or_filters = {}  # or_filters는 그대로 딕셔너리 형식을 유지합니다.

        order_by = None
        if isinstance(data.order_by, str):
            order_by = data.order_by
        elif isinstance(data.order_by, list):
            order_by = [f"{o.split('.')[0]} desc" if o.split(".")[-1] == "desc" else o for o in data.order_by]

        issues = await self.frappe_client.get_list(
            "Issue",
            filters=filters,  # 리스트 형태로 전달
            or_filters=or_filters,
            limit_start=data.page * data.size,
            limit_page_length=data.size,
            order_by=order_by,
        )
        return ERPNextIssuePaginatedResponse.model_validate({"items": issues}, from_attributes=True)

    async def get_contract(self, name: str):
        data = await self.frappe_client.get_doc("Contract", name)
        if not data:
            raise HTTPException(status_code=404, detail="contract not found")
        return ERPNextContract(**data)

    async def get_contracts(
        self,
        data: ERPNextContractRequest,
        sub: str,
    ):
        accessible_projects = await self.get_project_names(sub)

        if not accessible_projects:
            return ERPNextContractPaginatedResponse(items=[])

        accessible_projects_names = [p["project_name"] for p in accessible_projects]

        filters = {
            "document_type": ["=", "Project"],
            "document_name": accessible_projects_names,
            "status": ["!=", "Draft"],
        }
        or_filters = {}

        if data.keyword:
            filters["custom_name"] = ["like", f"%{data.keyword}%"]
        if data.start:
            filters["start_date"] = [">=", data.start]
        if data.end:
            filters["start_date"] = ["<=", data.end]
        if isinstance(data.project_id, str):
            if data.project_id not in accessible_projects_names:
                raise HTTPException(status_code=403, detail="Project not found")
            filters["document_name"] = ["=", data.project_id]
        elif isinstance(data.project_id, list):
            if not set(data.project_id).issubset(accessible_projects_names):
                raise HTTPException(status_code=403, detail="Project not found")
            filters["document_name"] = ["in", data.project_id]
        if isinstance(data.status, str):
            filters["status"] = ["=", data.status]
        elif isinstance(data.status, list):
            filters["status"] = ["in", data.status]

        order_by = ["modified asc"]
        if isinstance(data.order_by, str):
            order_by = data.order_by
        elif isinstance(data.order_by, list):
            order_by = [f"{o.split('.')[0]} desc" if o.split(".")[-1] == "desc" else o for o in data.order_by]

        contracts = await self.frappe_client.get_list(
            "Contract",
            filters=filters,
            or_filters=or_filters,
            limit_start=data.page * data.size,
            limit_page_length=data.size,
            order_by=order_by,
        )

        return ERPNextContractPaginatedResponse.model_validate({"items": contracts}, from_attributes=True)

    async def get_report_by_name(self, name: str):
        report = await self.frappe_client.get_doc("Project Report", name)

        if report:
            return ERPNextReport.model_validate(report)

    async def get_report_by_project_id(
        self,
        project_id: str,
        sub: str,
        start_date: datetime.date | str,
        end_date: datetime.date | str | None = None,
    ):
        project = await self.get_project_by_id(project_id, sub)
        filters = [
            ["Project Report", "project", "=", project.project_name],
            ["Project Report", "start_date", "=", start_date],
        ]

        if end_date:
            filters.append(["Project Report", "end_date", "=", end_date])

        reports = await self.frappe_client.get_list(
            "Project Report",
            filters=filters,
            limit_page_length=1,
        )

        if reports is None or len(reports) == 0:
            return None

        return ERPNextReport.model_validate(reports[0])

    async def get_timesheets(
        self,
        page: int,
        size: int,
        sub: str,
        project_id: str,
        start_date: datetime.date | str,
        end_date: datetime.date | str,
    ):
        project = await self.get_project_by_id(project_id, sub)

        timesheet = await self.frappe_client.get_list(
            "Timesheet",
            filters=[
                ["Timesheet", "end_date", ">=", start_date],
                ["Timesheet", "start_date", "<=", end_date],
                ["Timesheet", "parent_project", "=", project.project_name],
            ],
            limit_start=page * size,
            limit_page_length=size,
        )

        return ERPNextTimeSheetForUserList.model_validate({"items": timesheet}, from_attributes=True)

    async def get_file(self, project_id: str, key: str, task_id: str | None = None) -> ERPNextFile:
        filters = {"project": project_id}
        if task_id:
            filters["task"] = task_id

        data = await self.frappe_client.get_doc("Files", key, filters)
        return ERPNextFile(**data)

    async def get_files(
        self,
        project_id: str,
        page: int,
        size: int,
        order_by: str = "modified",
        task: str | None = None,
        issue: str | None = None,
    ):
        filters = {"project": project_id}

        if task:
            filters["task"] = task
        if issue:
            filters["issue"] = issue

        _order_by = None

        if order_by:
            if order_by.split(".")[-1] == "desc":
                _order_by = f"{order_by.split('.')[0]} desc"
            else:
                _order_by = order_by

        files = await self.frappe_client.get_list(
            "Files",
            filters=filters,
            limit_start=page * size,
            limit_page_length=size,
            order_by=_order_by,
        )

        return ERPNextFilesResponse.model_validate({"items": files}, from_attributes=True)

    async def get_slots(self, shift_types: list[str], task_types: list[str]):
        # ======================================================================
        # 1. 데이터 사전 로딩 및 필터링
        # ======================================================================
        all_shift_types = await self.frappe_client.get_list(
            "Shift Type",
            fields=["name", "start_time", "end_time"],
            filters={"name": ["in", shift_types]},
        )

        shift_type_map = {st["name"]: st for st in all_shift_types}

        if not shift_type_map:
            return []

        eligible_assignments = await self.frappe_client.get_list(
            "Shift Assignment",
            fields=["shift_type", "start_date", "end_date"],
            filters={"status": "Active", "shift_type": ["in", shift_types]},
        )

        if not eligible_assignments:
            return []

        parsed_assignments = [
            {
                "schedule": asn["shift_type"],
                "start_date": datetime.datetime.strptime(asn["start_date"], "%Y-%m-%d").date(),
                "end_date": datetime.datetime.strptime(asn["end_date"], "%Y-%m-%d").date(),
            }
            for asn in eligible_assignments
        ]

        # ======================================================================
        # 2. 계산 기간(start_date, end_date) 동적 결정
        # ======================================================================
        start_date = min(asn["start_date"] for asn in parsed_assignments)
        end_date = max(asn["end_date"] for asn in parsed_assignments)

        tasks = await self.frappe_client.get_list(
            "Task",
            filters={"type": ["in", task_types], "exp_end_date": [">=", start_date.isoformat()]},
            fields=["exp_start_date", "exp_end_date", "expected_time"],
        )

        # ======================================================================
        # 3. 날짜별 총 가용 시간 (Capacity) 계산
        # ======================================================================
        daily_capacity_hours = {}
        current_d = start_date
        while current_d <= end_date:
            daily_capacity_hours[current_d] = 0

            # 모든 배정(Assignment)을 순회
            for asn in parsed_assignments:
                # 현재 날짜가 이 배정의 유효 기간 안에 있는지 확인
                if asn["start_date"] <= current_d <= asn["end_date"]:
                    # 배정에 연결된 Shift Type 정보를 가져옴
                    shift_type_name = asn["schedule"]  # 사용자가 정의한 키 이름
                    shift_type_details = shift_type_map.get(shift_type_name)

                    if shift_type_details:
                        # 해당 Shift Type의 근무 시간을 계산
                        start_t = datetime.datetime.strptime(shift_type_details["start_time"], "%H:%M:%S").time()
                        end_t = datetime.datetime.strptime(shift_type_details["end_time"], "%H:%M:%S").time()
                        hours = (
                            datetime.datetime.combine(datetime.date.min, end_t)
                            - datetime.datetime.combine(datetime.date.min, start_t)
                        ).total_seconds() / 3600

                        # 그날의 총 가용 시간에 더함
                        daily_capacity_hours[current_d] += hours
            current_d += timedelta(days=1)

        # ======================================================================
        # 4. 예약된 Task 시간을 시작일에 모두 할당
        # ======================================================================
        booked_hours_by_day = {}
        for task in tasks:
            if not task.get("exp_start_date") or not task.get("expected_time") or task["expected_time"] == 0:
                continue

            task_start_dt = datetime.datetime.strptime(task["exp_start_date"], "%Y-%m-%d").date()
            booked_hours_by_day[task_start_dt] = booked_hours_by_day.get(task_start_dt, 0) + task["expected_time"]

        # ======================================================================
        # 5. 최종 결과 계산
        # ======================================================================
        available_slots_info = []
        today = datetime.date.today()
        current_date = start_date
        while current_date <= end_date:
            total_capacity = daily_capacity_hours.get(current_date, 0)
            if current_date < today:
                available_slots_info.append({"date": current_date.isoformat(), "remaining": "0"})
            else:
                if total_capacity >= 1:
                    booked_hours = booked_hours_by_day.get(current_date, 0)
                    available_hours = total_capacity - booked_hours
                    if available_hours >= 1:
                        remaining_percentage = (available_hours / total_capacity) * 100
                        available_slots_info.append(
                            {"date": current_date.isoformat(), "remaining": str(math.floor(remaining_percentage))}
                        )
            current_date += timedelta(days=1)

        return available_slots_info


# ... FrappUpdateRepository, FrappDeleteRepository, FrappeRepository는 기존 코드 유지 ...
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

        return ERPNextProjectForUser(**project)

    async def add_member_to_project(self, data: ERPNextProjectForUser, sub: str, level: int):
        project = await self.frappe_client.update(
            {
                "doctype": "Project",
                "name": data.project_name,
                "custom_team": json.dumps(
                    [d.model_dump() for d in data.custom_team] + [{"member": sub, "level": level if level > 0 else 1}]
                ),
            }
        )

        return ERPNextProjectForUser(**project)

    async def edit_project_member(self, project_id: str, data: list[ERPNextTeam]):
        project = await self.frappe_client.update(
            {
                "doctype": "Project",
                "name": project_id,
                "custom_team": json.dumps([d.model_dump() for d in data]),
            }
        )

        return ERPNextProjectForUser(**project)

    async def update_issue_by_id(self, name: str, data: UpdateERPNextIssue):
        updated_issue = await self.frappe_client.update(
            {
                "doctype": "Issue",
                "name": name,
                **data.model_dump(by_alias=True, exclude_unset=True),
            }
        )

        return ERPNextIssue(**updated_issue)

    async def update_contract_by_id(self, name: str, data: UpdateERPNextContract):
        updated_contract = await self.frappe_client.update(
            {
                "doctype": "Contract",
                "name": name,
                **data.model_dump(by_alias=True, exclude_unset=True),
            }
        )

        return ERPNextContract(**updated_contract)

    async def update_report(
        self,
        name: str,
        project_id: str | None = None,
        start_date: datetime.date | str | None = None,
        end_date: datetime.date | str | None = None,
        summary: str | None = None,
    ):
        update_doc = {
            "doctype": "Project Report",
            "name": name,
        }

        if project_id is not None:
            update_doc["project"] = project_id
        if start_date is not None:
            update_doc["start_date"] = start_date
        if end_date is not None:
            update_doc["end_date"] = end_date
        if summary is not None:
            update_doc["summary"] = summary

        report = await self.frappe_client.update(update_doc)

        return ERPNextReport.model_validate(report)


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

    async def delete_issue_by_id(self, name: str):
        await self.frappe_client.delete("Issue", name)

    async def delete_file(self, key: str):
        await self.frappe_client.delete("Files", key)


class FrappeRepository(
    FrappCreateRepository,
    FrappReadRepository,
    FrappUpdateRepository,
    FrappDeleteRepository,
):
    pass
