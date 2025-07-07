import asyncio
import json
from datetime import date, datetime, timedelta
from logging import getLogger
from typing import Annotated

import openai
from fastapi import HTTPException, Path, Query, status
from keycloak import KeycloakAdmin

from src.app.fellows.data.project import *
from src.app.fellows.repository.frappe import FrappeRepository
from src.app.fellows.schema.project import *
from src.core.dependencies.auth import get_current_user
from src.core.utils.frappeclient import AsyncFrappeClient

logger = getLogger(__name__)


class ProjectService:
    """
    프로젝트 관련 비즈니스 로직을 처리하는 서비스 클래스입니다.

    권한 레벨:
        - 0: 소유주 (모든 권한)
        - 1: 관리자 (소유주 제외 대부분의 관리 권한)
        - 2: 기본 멤버 (프로젝트, 태스크, 이슈 등 RW, 그룹 탈퇴)
        - 3: 읽기 전용 멤버 (R, 그룹 탈퇴)
        - 4: 제한된 멤버 (접근 불가, 그룹 탈퇴만 가능)
    """

    def __init__(
        self,
        openai_client: openai.AsyncOpenAI,
        frappe_client: AsyncFrappeClient,
        frappe_repository: FrappeRepository,
        keycloak_admin: KeycloakAdmin,
    ):
        self.openai_client = openai_client
        self.frappe_client = frappe_client
        self.frappe_repository = frappe_repository
        self.keycloak_admin = keycloak_admin

    async def create_project(
        self,
        data: CreateERPNextProject,
        user: get_current_user,
    ) -> UserERPNextProject:
        """
        새로운 프로젝트를 생성합니다.

        프로젝트를 생성하는 사용자는 자동으로 소유주(level 0)가 됩니다.

        Args:
            data: 생성할 프로젝트의 데이터.
            user: 현재 인증된 사용자 정보.

        Returns:
            생성된 프로젝트의 정보.
        """
        await self.frappe_repository.get_or_create_customer(user)
        return await self.frappe_repository.create_project(data, user.sub)

    async def get_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ) -> UserERPNextProject:
        """
        특정 프로젝트의 상세 정보를 조회합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-3만 접근 가능.
            project_id: 조회할 프로젝트의 ID.

        Returns:
            프로젝트의 상세 정보.

        Raises:
            HTTPException: 사용자가 프로젝트 멤버가 아니거나 권한 레벨이 4일 경우 발생.
        """
        return await self.frappe_repository.get_project_by_id(project_id, user.sub)

    async def get_projects(
        self,
        data: Annotated[ERPNextProjectsRequest, Query()],
        user: get_current_user,
    ) -> ProjectsPaginatedResponse:
        """
        사용자가 속한 프로젝트 목록을 조회합니다.

        Args:
            data: 페이지네이션 및 필터링 옵션.
            user: 현재 인증된 사용자 정보. 권한 레벨 0-3의 프로젝트만 조회됩니다.

        Returns:
            프로젝트 목록과 페이지네이션 정보.
        """
        return await self.frappe_repository.get_projects(data, user.sub)

    async def get_projects_overview(
        self,
        user: get_current_user,
    ):
        """
        사용자가 속한 프로젝트의 개요 목록을 조회합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-3의 프로젝트만 조회됩니다.

        Returns:
            프로젝트 개요 목록.
        """
        return await self.frappe_repository.get_projects_overview(user.sub)

    async def update_project_info(
        self,
        data: UpdateERPNextProject,
        user: get_current_user,
        project_id: str = Path(),
    ) -> UserERPNextProject:
        """
        프로젝트의 기본 정보를 수정합니다.

        Args:
            data: 수정할 프로젝트 정보.
            user: 현재 인증된 사용자 정보. 권한 레벨 0-2까지 허용됩니다.
            project_id: 수정할 프로젝트의 ID.

        Returns:
            수정된 프로젝트 정보.

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 2) 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

        if level > 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update project information.",
            )

        return await self.frappe_repository.update_project_by_id(project.project_name, data)

    async def add_members_to_project(
        self,
        email: Annotated[str, Query()],
        user: get_current_user,
        project_id: str = Path(),
    ):
        """
        프로젝트에 새로운 멤버를 초대합니다.

        초대된 멤버는 기본적으로 권한 레벨 4(제한된 멤버)로 설정됩니다.

        Args:
            email: 초대할 사용자의 이메일.
            user: 현재 인증된 사용자 정보. 권한 레벨 0-1까지 허용됩니다.
            project_id: 멤버를 추가할 프로젝트의 ID.

        Returns:
            멤버가 추가된 후의 프로젝트 정보.

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 1) 또는 초대할 유저가 존재하지 않거나 이미 멤버일 경우 발생.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

        if level > 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to add members."
            )

        invited_user = await self.keycloak_admin.a_get_users({"email": email})
        if not invited_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that email not found.")
        sub = invited_user[0]["id"]

        if any([t.member == sub for t in project.custom_team]):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User is already a member of this project."
            )

        return await self.frappe_repository.add_member_to_project(project, sub, 4)

    async def update_project_team(
        self,
        data: list[ERPNextTeam],
        user: get_current_user,
        project_id: str = Path(),
    ):
        """
        프로젝트 팀 멤버의 권한 레벨을 수정하거나 멤버를 내보냅니다.

        - 소유주(0): 자기 자신을 제외한 모든 멤버의 권한을 수정할 수 있습니다.
        - 관리자(1): 자기 자신보다 낮은 레벨의 멤버(2, 3, 4)만 수정할 수 있습니다.
        - 초대된 멤버(4): 오직 본인만 팀에서 나갈 수 있습니다(리스트에서 자신을 제거). 다른 사용자는 레벨 4 멤버를 수정할 수 없습니다.

        Args:
            data: 수정할 팀 멤버 정보 리스트.
            user: 현재 인증된 사용자 정보.
            project_id: 팀을 수정할 프로젝트의 ID.

        Returns:
            팀 정보가 수정된 프로젝트 정보.

        Raises:
            HTTPException: 권한 규칙에 어긋날 경우 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

        if level > 1 and level != 4:  # 소유자, 관리자, 레벨4 멤버 외에는 수정 불가
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to edit the team."
            )

        for member_update in data:
            original_member = next((m for m in project.custom_team if m.member == member_update.member), None)

            # 레벨 4 멤버에 대한 권한 검사
            if original_member and original_member.level == 4:
                if member_update.member != user.sub:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only the invited user (level 4) can modify their own status.",
                    )

            # 소유주(0) 권한 검사
            if level == 0:
                if member_update.member == user.sub and member_update.level != 0:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="Owner cannot change their own level."
                    )
            # 관리자(1) 권한 검사
            elif level == 1:
                if original_member and original_member.level <= level:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Admins cannot change members with the same or higher level.",
                    )
                if member_update.level <= level:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Admins can only assign levels lower than their own.",
                    )

        # 공통 규칙 검증
        if not any(member.member == project.customer for member in data):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="The project owner must remain in the team."
            )
        if any(member.member == project.customer and member.level != 0 for member in data):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The project owner's level must be 0.")
        if any(member.member != project.customer and member.level < 1 for member in data):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Team members cannot be assigned level 0."
            )

        return await self.frappe_repository.edit_project_member(project.project_name, data)

    async def delete_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ):
        """
        프로젝트를 삭제합니다.

        연관된 모든 태스크, 이슈, 파일도 함께 삭제됩니다.

        Args:
            user: 현재 인증된 사용자 정보. 소유주(level 0)만 허용됩니다.
            project_id: 삭제할 프로젝트의 ID.

        Raises:
            HTTPException: 권한이 부족할 경우 (level != 0) 또는 프로젝트가 삭제 불가능할 경우 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

        if not project.custom_deletable:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This project cannot be deleted.")

        if level != 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can delete the project."
            )

        return await self.frappe_repository.delete_project_by_id(project.project_name)

    async def get_quote_slots(self) -> list[QuoteSlot]:
        """
        견적 상담이 가능한 시간 슬롯을 조회합니다.

        Returns:
            사용 가능한 날짜와 남은 용량(%) 정보 리스트.
        """
        return await self.frappe_repository.get_slots(
            ["Fellows Manager"],
            ["Quote Review"],
        )

    async def submit_project(
        self,
        user: get_current_user,
        data: Annotated[Quote, Query()],
        project_id: str = Path(),
    ) -> None:
        """
        프로젝트를 검토 단계로 제출합니다.

        제출 시 견적 검토를 위한 태스크가 생성됩니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-1까지 허용됩니다.
            data: 인바운드 여부 및 희망 상담 날짜 정보.
            project_id: 제출할 프로젝트의 ID.

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 1) 또는 프로젝트 상태가 'draft'가 아닐 경우 발생.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

        if level > 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to submit this project."
            )

        result = await self.frappe_client.get_list(
            "Project",
            fields=["project_name"],
            filters={"customer": user.sub, "custom_project_status": ["like", "%process%"]},
        )
        if len(result) >= 10:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

        managers = await self.frappe_client.get_doc("User Group", "Managers")
        if project.custom_project_status != "draft":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        quote_slots = await self.frappe_repository.get_slots(
            ["Fellows Manager"],
            ["Quote Review"],
        )
        if data.date:
            vaild = list(filter(lambda d: d["date"] == data.date.strftime("%Y-%m-%d"), quote_slots))
            if not vaild:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
            quote_date = vaild[0]["date"]
        else:
            quote_date = sorted(quote_slots, key=lambda x: x["date"])[0]["date"]
        quote_date = datetime.strptime(quote_date, "%Y-%m-%d").date()
        await self.frappe_repository.update_project_by_id(
            project_id,
            UpdateERPNextProject(
                custom_project_status=CustomProjectStatus.PROCESS_1,
                is_active=IsActive.YES,
            ),
        )
        task = await self.frappe_repository.create_task(
            ERPNextTask(
                subject="프로젝트 견적 확인",
                project=project_id,
                color="#FF4500",
                is_group=True,
                is_template=False,
                custom_is_user_visible=True,
                status="Open",
                priority="High",
                task_weight=1.0,
                exp_start_date=quote_date,
                exp_end_date=quote_date + timedelta(days=3),
                expected_time=8.0 if data.inbound else 4.0,
                duration=3,
                is_milestone=True,
                description="프로젝트 요구사항 분석 및 견적 내부 검토 상담이 진행된 다음 견적가를 알려드릴께요"
                if data.inbound
                else "프로젝트 요구사항 분석 및 견적 내부 검토 후 실제 견적가를 알려드릴께요",
                department="Management",
                company="Fellows",
                type="Quote Review",
            ),
            user.sub,
        )
        await self.frappe_repository.create_todo_many(
            [
                ERPNextToDo(
                    priority=ERPNextToDoPriority.HIGH,
                    color="#FF4500",
                    allocated_to=manager["user"],
                    description=f"Allocated Initial Planning and Vendor Quotation Review Task for {project_id}",
                    reference_type="Task",
                    reference_name=task.name,
                )
                for manager in managers["user_group_members"]
            ]
        )

    async def cancel_submit_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ):
        """
        제출된 프로젝트를 다시 초안(draft) 상태로 되돌립니다.

        생성되었던 견적 검토 태스크는 모두 삭제됩니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-1까지 허용됩니다.
            project_id: 제출을 취소할 프로젝트의 ID.

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 1) 또는 프로젝트 상태가 'process:1'이 아닐 경우 발생.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

        if level > 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to cancel project submission."
            )

        if project.custom_project_status != CustomProjectStatus.PROCESS_1:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await self.frappe_repository.update_project_by_id(
            project_id,
            UpdateERPNextProject(
                custom_project_status=CustomProjectStatus.DRAFT,
                is_active=IsActive.NO,
            ),
        )
        tasks = await self.frappe_client.get_list("Task", fields=["name"], filters={"project": project_id})
        await self.frappe_client.bulk_update(
            [
                {
                    "doctype": "Task",
                    "docname": task.get("name"),
                    "parent_task": None,
                    "depends_on": [],
                    "depends_on_tasks": [],
                }
                for task in tasks
            ]
        )
        await asyncio.gather(*[self.frappe_repository.delete_task_by_id(task.get("name")) for task in tasks])

    async def create_file(
        self,
        user: get_current_user,
        data: ERPNextFile,
        project_id: str = Path(),
    ) -> ERPNextFile:
        """
        프로젝트에 파일을 업로드(생성)합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-2까지 허용됩니다.
            data: 생성할 파일 정보.
            project_id: 파일을 추가할 프로젝트의 ID.

        Returns:
            생성된 파일 정보.

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 2) 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)
        if level > 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create files in this project.",
            )

        payload = ERPNextFile(**data.model_dump(exclude={"project"}), project=project.project_name)
        return await self.frappe_repository.create_file(payload)

    async def read_file(
        self,
        user: get_current_user,
        project_id: str = Path(),
        key: str = Path(),
    ) -> ERPNextFile:
        """
        프로젝트 내 특정 파일의 정보를 조회합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-3까지 허용됩니다.
            project_id: 파일이 속한 프로젝트의 ID.
            key: 조회할 파일의 고유 키.

        Returns:
            파일 정보.

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 3) 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)
        if level > 3:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to read files in this project.",
            )

        return await self.frappe_repository.get_file(project.project_name, key)

    async def read_files(
        self,
        user: get_current_user,
        data: Annotated[ERPNextFileRequest, Query()],
        project_id: str = Path(),
    ) -> ERPNextFilesResponse:
        """
        프로젝트 내 파일 목록을 조회합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-3까지 허용됩니다.
            data: 페이지네이션 및 필터링 옵션.
            project_id: 파일 목록을 조회할 프로젝트의 ID.

        Returns:
            파일 목록과 페이지네이션 정보.

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 3) 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)
        if level > 3:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to read files in this project.",
            )

        return await self.frappe_repository.get_files(project.project_name, data)

    async def delete_file(
        self,
        user: get_current_user,
        project_id: str = Path(),
        key: str = Path(),
    ):
        """
        프로젝트 내 파일을 삭제합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-2까지 허용됩니다.
            project_id: 파일이 속한 프로젝트의 ID.
            key: 삭제할 파일의 고유 키.

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 2) 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)
        if level > 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete files in this project.",
            )

        await self.frappe_repository.delete_file(key)

    async def read_tasks(
        self,
        user: get_current_user,
        data: Annotated[ERPNextTasksRequest, Query()],
    ) -> ERPNextTaskPaginatedResponse:
        """
        사용자가 접근 가능한 태스크 목록을 조회합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-3의 프로젝트에 속한 태스크만 조회됩니다.
            data: 페이지네이션 및 필터링 옵션.

        Returns:
            태스크 목록과 페이지네이션 정보.
        """
        return await self.frappe_repository.get_tasks(data, user.sub)

    async def create_issue(
        self,
        user: get_current_user,
        data: CreateERPNextIssue,
    ):
        """
        프로젝트에 새로운 이슈를 생성합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-2까지 허용됩니다.
            data: 생성할 이슈의 정보.

        Returns:
            생성된 이슈 정보.

        Raises:
            HTTPException: 이슈를 생성하려는 프로젝트에 대한 권한이 부족할 경우 (level > 2) 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(data.project, user.sub)
        if level > 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create issues in this project.",
            )

        return await self.frappe_repository.create_issue(data, user.sub)

    async def read_issues(
        self,
        user: get_current_user,
        data: Annotated[ERPNextIssuesRequest, Query()],
    ):
        """
        사용자가 접근 가능한 이슈 목록을 조회합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-3의 프로젝트에 속한 이슈만 조회됩니다.
            data: 페이지네이션 및 필터링 옵션.

        Returns:
            이슈 목록과 페이지네이션 정보.
        """
        return await self.frappe_repository.get_issues(data, user.sub)

    async def update_issue(
        self,
        user: get_current_user,
        data: UpdateERPNextIssue,
        name: str = Path(),
    ):
        """
        특정 이슈를 수정합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-2까지 허용됩니다.
            data: 수정할 이슈 정보.
            name: 수정할 이슈의 이름(ID).

        Returns:
            수정된 이슈 정보.

        Raises:
            HTTPException: 이슈를 수정하려는 프로젝트에 대한 권한이 부족할 경우 (level > 2) 발생합니다.
        """
        issue = await self.frappe_repository.get_issue(name)
        project, level = await self.frappe_repository.get_user_project_permission(issue.project, user.sub)

        if level > 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update issues in this project.",
            )

        return await self.frappe_repository.update_issue_by_id(issue.name, data)

    async def delete_issue(
        self,
        user: get_current_user,
        name: str = Path(),
    ):
        """
        특정 이슈를 삭제합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-2까지 허용됩니다.
            name: 삭제할 이슈의 이름(ID).

        Raises:
            HTTPException: 이슈를 삭제하려는 프로젝트에 대한 권한이 부족할 경우 (level > 2) 발생합니다.
        """
        issue = await self.frappe_repository.get_issue(name)
        project, level = await self.frappe_repository.get_user_project_permission(issue.project, user.sub)

        if level > 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete issues in this project.",
            )

        return await self.frappe_repository.delete_issue_by_id(issue.name)

    async def get_project_feature_estimate(
        self,
        user: get_current_user,
        project_base: Annotated[ProjectFeatureEstimateRequest, Query()],
    ):
        """
        AI를 사용하여 프로젝트의 주요 기능 목록을 예측합니다.

        Args:
            user: 현재 인증된 사용자 정보.
            project_base: 프로젝트의 기본 정보.

        Returns:
            예측된 기능 이름의 리스트.
        """
        payload = project_base.model_dump_json()

        response = await self.openai_client.responses.create(
            model="gpt-4.1-mini",
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
        """
        AI를 사용하여 프로젝트의 견적을 스트림 방식으로 생성합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-2까지 허용됩니다.
            project_id: 견적을 생성할 프로젝트의 ID.

        Yields:
            Server-Sent Events (SSE) 스트림.

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 2) 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

        if level > 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to get AI estimate for this project.",
            )

        if project.custom_project_status != "draft" and project.custom_project_status != "process:1":
            return

        payload = json.dumps(
            {
                "프로젝트 이름": project.custom_project_title,
                "프로젝트 설명": project.custom_project_summary,
                "플랫폼": [item.platform for item in project.custom_platforms],
                "준비 정도": project.custom_readiness_level,
                "시작일": project.expected_start_date,
                "종료일": project.expected_end_date,
                "유지 보수 필요": project.custom_maintenance_required,
                "예상 페이지 수": project.custom_content_pages,
                "기능": [item.feature for item in project.custom_features],
            },
            default=str,
            ensure_ascii=False,
        )

        stream = await self.openai_client.responses.create(
            model="o4-mini",
            instructions=estimation_instruction,
            input=payload,
            max_output_tokens=10000,
            top_p=1.0,
            stream=True,
        )
        yield "event: ping\n"

        async for event in stream:
            if event.type == "response.output_text.delta":
                for chunk in event.delta.splitlines():
                    yield f"data: {chunk}\n"
                if event.delta.endswith("\n"):
                    yield "data: \n"
                yield "\n"
            elif event.type == "response.output_text.done":
                yield "event: stream_done\n"
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
        """
        AI 견적 결과로부터 이모지와 총금액을 추출합니다.

        Args:
            ai_estimate: AI가 생성한 전체 견적 텍스트.

        Returns:
            (emoji, total_amount) 튜플.
        """
        response = await self.openai_client.responses.create(
            model="gpt-4.1-mini",
            instructions=project_information_instruction,
            input=ai_estimate,
            max_output_tokens=100,
            top_p=1.0,
        )

        result = [s.strip() for s in response.output_text.split(",")]

        emoji = result[0]
        total_amount = int(result[1])

        return emoji, total_amount
