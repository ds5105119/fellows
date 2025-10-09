import asyncio
import json
from datetime import datetime, timedelta
from logging import getLogger
from typing import Annotated

import openai
from fastapi import HTTPException, Path, Query, status
from keycloak import KeycloakAdmin
from webtool.cache import RedisCache

from src.app.fellows.data.project import *
from src.app.fellows.repository.frappe import FrappeRepository
from src.app.fellows.schema.project import (
    CreateERPNextIssue,
    CreateERPNextProject,
    CustomProjectStatus,
    ERPNextFile,
    ERPNextFileRequest,
    ERPNextFilesResponse,
    ERPNextIssuesRequest,
    ERPNextProjectForUser,
    ERPNextProjectsRequest,
    ERPNextTask,
    ERPNextTaskPaginatedResponse,
    ERPNextTasksRequest,
    ERPNextTeam,
    ERPNextToDo,
    ERPNextToDoPriority,
    IsActive,
    ProjectFeatureEstimateRequest,
    ProjectsPaginatedResponse,
    ProjectSummary2InfoResponse,
    Quote,
    QuoteSlot,
    UpdateERPNextCustomer,
    UpdateERPNextIssue,
    UpdateERPNextProject,
)
from src.app.user.repository.alert import AlertRepository
from src.app.user.schema.user_data import ProjectAdminUserAttributes
from src.app.user.service.cloud import CloudService
from src.core.dependencies.auth import get_current_user
from src.core.dependencies.db import db_session
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
        cloud_service: CloudService,
        frappe_repository: FrappeRepository,
        alert_repository: AlertRepository,
        keycloak_admin: KeycloakAdmin,
        redis_cache: RedisCache,
    ):
        self.openai_client = openai_client
        self.frappe_client = frappe_client
        self.cloud_service = cloud_service
        self.frappe_repository = frappe_repository
        self.alert_repository = alert_repository
        self.keycloak_admin = keycloak_admin
        self.redis_cache = redis_cache

    async def create_project(
        self,
        data: CreateERPNextProject,
        user: get_current_user,
    ) -> ERPNextProjectForUser:
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
    ) -> ERPNextProjectForUser:
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

    async def get_project_admin(self, user: get_current_user, project_id: str = Path()) -> ProjectAdminUserAttributes:
        """
        특정 프로젝트의 소유자를 확인합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 0-3만 접근 가능.
            project_id: 조회할 프로젝트의 ID.

        Returns:
            프로젝트의 소유자 상세 정보.

        Raises:
            HTTPException: 사용자가 프로젝트 멤버가 아니거나 권한 레벨이 4일 경우 발생.
        """
        project = await self.frappe_repository.get_project_by_id(project_id, user.sub)
        data = await self.keycloak_admin.a_get_user(project.customer)

        return ProjectAdminUserAttributes.model_validate(
            data["attributes"]
            | {
                "email": data["email"],
                "sub": data["id"],
            }
        )

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
    ) -> ERPNextProjectForUser:
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
        session: db_session,
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
            None

        Raises:
            HTTPException: 권한이 부족할 경우 (level > 1) 또는 초대할 유저가 존재하지 않거나 이미 멤버일 경우 발생.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

        if len(project.custom_team) > 5:
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED)

        if level > 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to add members."
            )

        invited_user = await self.keycloak_admin.a_get_users({"email": email})
        if not invited_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that email not found.")
        sub = invited_user[0]["id"]

        project_invited_user = list(filter(lambda m: m.member == sub, project.custom_team))

        if project_invited_user:
            if project_invited_user[0].level != 4:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="This member is already joined.")
        else:
            await self.frappe_repository.add_member_to_project(project, sub, 4)

        await self.alert_repository.create(
            session,
            sub=sub,
            message=f"{user.name}님에게 {project.custom_project_title} 프로젝트에 초대되었습니다.",
            link=f"/service/project/{project.project_name}",
        )

    async def accept_invite_to_project(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ):
        """
        초대를 수락합니다.

        Args:
            user: 현재 인증된 사용자 정보. 권한 레벨 4 허용됩니다.
            project_id: 초대된 프로젝트의 ID.

        Returns:
            멤버가 추가된 후의 프로젝트 정보.

        Raises:
            HTTPException: 권한이 부족할 경우 (level !=4) 경우 발생.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

        if level != 4:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to accept.")

        payload = list(filter(lambda m: m.member != user.sub, project.custom_team))
        payload.append(ERPNextTeam.model_validate({"member": user.sub, "level": 3}))

        return await self.frappe_repository.edit_project_member(project.project_name, payload)

    async def update_project_team(
        self,
        data: list[ERPNextTeam],
        user: get_current_user,
        project_id: str = Path(),
    ):
        """
        프로젝트 팀 멤버의 권한 레벨을 수정하거나 멤버를 팀에서 삭제합니다.

        - 소유주(0): 자기 자신을 제외한 모든 멤버의 권한을 수정하거나 삭제할 수 있습니다.
        - 관리자(1): 자기 자신보다 낮은 레벨(2, 3, 4)의 멤버만 수정하거나 삭제할 수 있습니다.
        - 초대된 멤버(4) 및 기타 멤버: 오직 본인만 팀에서 나갈 수 있습니다(리스트에서 자신을 제거).

        Args:
            data: 수정 후의 최종 팀 멤버 정보 리스트.
            user: 현재 인증된 사용자 정보.
            project_id: 팀을 수정할 프로젝트의 ID.

        Returns:
            팀 정보가 수정된 프로젝트 정보.

        Raises:
            HTTPException: 권한 규칙에 어긋날 경우 발생합니다.
        """
        project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)
        original_members_map = {member.member: member for member in project.custom_team}
        new_member_ids = {member.member for member in data}

        # 1. 멤버 삭제 권한 검증
        deleted_member_ids = set(original_members_map.keys()) - new_member_ids
        for deleted_id in deleted_member_ids:
            # 자기 자신을 삭제하는 것은 항상 허용 (그룹 탈퇴)
            if deleted_id == user.sub:
                continue

            member_to_delete = original_members_map[deleted_id]

            # 소유주(0)는 누구든 삭제 가능 (자기 자신은 이 루프에 들어오지 않음)
            if level == 0:
                continue

            # 관리자(1)는 자기보다 낮은 레벨만 삭제 가능
            if level == 1:
                if member_to_delete.level > level:
                    continue
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Admins cannot delete members with the same or higher level.",
                    )

            # 그 외 레벨(2, 3, 4)은 다른 사람을 삭제할 수 없음
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete other members.",
            )

        # 2. 멤버 권한 수정 검증
        for member_update in data:
            original_member = original_members_map.get(member_update.member)

            # 새롭게 추가된 멤버는 이 API에서 처리하지 않음 (add_members_to_project 사용)
            if not original_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot add new member '{member_update.member}' via this endpoint. Use the add member endpoint.",
                )

            # 권한 레벨이 변경된 경우에만 검사
            if original_member.level != member_update.level:
                # 레벨 4 멤버의 권한은 소유주나 관리자만 변경 가능
                if original_member.level == 4 and level > 1:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only admins or the owner can change the level of an invited member.",
                    )

                # 소유주(0) 권한 검사
                if level == 0:
                    if member_update.member == user.sub:  # 소유주 자신의 레벨 변경 시도
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN, detail="Owner cannot change their own level."
                        )
                # 관리자(1) 권한 검사
                elif level == 1:
                    if original_member.level <= level:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admins cannot change members with the same or higher level.",
                        )
                    if member_update.level <= level:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admins can only assign levels lower than their own.",
                        )
                # 그 외 레벨(2, 3, 4)은 누구의 권한도 변경할 수 없음
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You do not have permission to change member levels.",
                    )

        # 3. 최종 팀 구성 규칙 검증
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

        files = await self.frappe_repository.get_files(project_id, page=0, size=1000)
        await self.cloud_service.delete_files(files)

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

        if not quote_slots or all(slot["remaining"] == "0" for slot in quote_slots):
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

        if data.date:
            vaild = list(filter(lambda d: d["date"] == data.date.strftime("%Y-%m-%d"), quote_slots))
            if not vaild:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
            quote_date = vaild[0]["date"]
        else:
            quote_date = sorted(quote_slots, key=lambda x: x["date"])[0]["date"]
        quote_date = datetime.strptime(quote_date, "%Y-%m-%d").date()

        if project.expected_end_date and quote_date > project.expected_end_date:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

        await self.frappe_repository.update_project_by_id(
            project_id,
            UpdateERPNextProject(
                custom_project_status=CustomProjectStatus.PROCESS_1,
                expected_start_date=quote_date,
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

        is_loading = await self.redis_cache.get("project_file_upload" + project_id + data.key)

        if is_loading == b"1":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        await self.redis_cache.set("project_file_upload" + project_id + data.key, b"1", 60 * 10)

        try:
            payload = ERPNextFile(**data.model_dump(exclude={"project"}), project=project.project_name)
            return await self.frappe_repository.create_file(payload)
        finally:
            await self.redis_cache.delete("project_file_upload" + project_id + data.key)

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

        return await self.frappe_repository.get_files(project_id=project.project_name, **data.model_dump())

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

        return await self.frappe_repository.get_tasks(**data.model_dump(), sub=user.sub)

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

    async def get_customer(self, user: get_current_user):
        return await self.frappe_repository.get_or_create_customer(user)

    async def update_customer(self, user: get_current_user, data: UpdateERPNextCustomer):
        return await self.frappe_repository.update_customer_by_id(user.sub, data)

    async def generate_project_info_by_summary(
        self,
        user: get_current_user,
        project_summary: Annotated[str, Query()],
    ) -> ProjectSummary2InfoResponse:
        """
        AI를 사용하여 프로젝트의 주요 기능 목록을 예측합니다.

        Args:
            user: 현재 인증된 사용자 정보.
            project_summary: 프로젝트 설명.

        Returns:
            예측된 기능 이름의 리스트.
        """
        response = await self.openai_client.responses.create(
            model="gpt-4.1-mini",
            instructions=description_to_title_instruction,
            input=project_summary,
            max_output_tokens=1000,
            top_p=1.0,
        )

        result = response.output_text

        return ProjectSummary2InfoResponse.model_validate_json(result)

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
            model="gpt-5-mini",
            instructions=feature_estimate_instruction,
            input=payload,
            max_output_tokens=2000,
            top_p=1.0,
        )

        result = [s.strip() for s in response.output_text.split(",")]

        return result

    async def get_project_estimate_status(
        self,
        user: get_current_user,
        project_id: str = Path(),
    ) -> bool:
        is_loading = await self.redis_cache.get("project_estimate" + project_id)

        if is_loading == b"1":
            return True

        return False

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
        is_loading = await self.redis_cache.get("project_estimate" + project_id)

        if is_loading == b"1":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        await self.redis_cache.set("project_estimate" + project_id, b"1", 60 * 10)

        try:
            project, level = await self.frappe_repository.get_user_project_permission(project_id, user.sub)

            if level > 2:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to get AI estimate for this project.",
                )

            if project.custom_project_status != "draft" and project.custom_project_status != "process:1":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to get AI estimate for this project.",
                )

            obj = {
                "프로젝트 이름": project.custom_project_title,
                "프로젝트 설명": project.custom_project_summary,
                "프로젝트 진행 방법": project.custom_project_method,
                "플랫폼": [item.platform for item in project.custom_platforms],
                "준비 정도": project.custom_readiness_level,
                "시작일": project.expected_start_date,
                "종료일": project.expected_end_date,
                "예상 페이지 수": project.custom_content_pages,
            }

            if project.custom_project_method == "code":
                obj["기능"] = [item.feature for item in project.custom_features]

            if project.custom_nocode_platform:
                obj["노코드 플랫폼"] = project.custom_nocode_platform

            payload = json.dumps(
                obj,
                default=str,
                ensure_ascii=False,
            )

            stream = await self.openai_client.responses.create(
                model="o4-mini",
                instructions=estimation_instruction,
                input=payload,
                max_output_tokens=10000,
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

        except Exception as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)

        finally:
            await self.redis_cache.delete("project_estimate" + project_id)

    async def project_estimate_after_job(self, ai_estimate: str):
        """
        AI 견적 결과로부터 이모지와 총금액을 추출합니다.

        Args:
            ai_estimate: AI가 생성한 전체 견적 텍스트.

        Returns:
            (emoji, total_amount) 튜플.
        """
        response = await self.openai_client.responses.create(
            model="gpt-5-mini",
            instructions=project_information_instruction,
            input=ai_estimate,
            max_output_tokens=1000,
            top_p=1.0,
        )

        result = [s.strip() for s in response.output_text.split(",")]

        emoji = result[0]
        total_amount = int(result[1])

        return emoji, total_amount
