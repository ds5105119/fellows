import calendar
from logging import getLogger
from typing import Annotated

import openai
from fastapi import HTTPException, Path, Query, status
from keycloak import KeycloakAdmin
from webtool.cache import RedisCache

from src.app.fellows.data.project import *
from src.app.fellows.repository.report import ReportRepository
from src.app.fellows.schema.report import (
    DailyReportRequest,
    ReportResponse,
)
from src.app.user.repository.alert import AlertRepository
from src.app.user.service.cloud import CloudService
from src.core.dependencies.auth import get_current_user

logger = getLogger(__name__)


class ReportService:
    def __init__(
        self,
        openai_client: openai.AsyncOpenAI,
        cloud_service: CloudService,
        report_repository: ReportRepository,
        alert_repository: AlertRepository,
        keycloak_admin: KeycloakAdmin,
        redis_cache: RedisCache,
    ):
        self.openai_client = openai_client
        self.cloud_service = cloud_service
        self.report_repository = report_repository
        self.alert_repository = alert_repository
        self.keycloak_admin = keycloak_admin
        self.redis_cache = redis_cache

    async def get_daily_report(
        self,
        user: get_current_user,
        data: Annotated[DailyReportRequest, Query()],
        project_id: str | None = Path(),
    ) -> ReportResponse:
        report = await self.report_repository.get_report_by_project_id(project_id, user.sub, data.date)

        tasks = await self.report_repository.get_tasks(
            0,
            1000,
            user.sub,
            project_id=project_id,
            start=data.date,
            end=data.date,
        )

        timesheets = await self.report_repository.get_timesheets(
            0,
            100,
            user.sub,
            project_id=project_id,
            start_date=data.date,
            end_date=data.date,
        )

        if not report:
            report = await self.report_repository.create_report(project_id, data.date, data.date, "")

        return ReportResponse.model_validate(
            {
                "report": report,
                "tasks": tasks.items,
                "timesheets": timesheets.items,
            },
            from_attributes=True,
        )

    async def get_monthly_report(
        self,
        user: get_current_user,
        data: Annotated[DailyReportRequest, Query()],
        project_id: str | None = Path(),
    ) -> ReportResponse:
        last_day = calendar.monthrange(data.date.year, data.date.month)[1]
        start_date = data.date.replace(day=1)
        end_date = data.date.replace(day=last_day)

        report = await self.report_repository.get_report_by_project_id(project_id, user.sub, start_date, end_date)

        tasks = await self.report_repository.get_tasks(
            0,
            1000,
            user.sub,
            project_id=project_id,
            start=start_date,
            end=end_date,
        )

        timesheets = await self.report_repository.get_timesheets(
            0,
            100,
            user.sub,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
        )

        if not report:
            report = await self.report_repository.create_report(project_id, start_date, end_date, "")

        return ReportResponse.model_validate(
            {
                "report": report,
                "tasks": tasks.items,
                "timesheets": timesheets.items,
            },
            from_attributes=True,
        )

    async def get_report_summary_status(
        self,
        user: get_current_user,
        report_id: str = Path(),
    ) -> bool:
        is_loading = await self.redis_cache.get(report_id)

        if is_loading == b"1":
            return True

        return False

    async def get_report_summary(
        self,
        user: get_current_user,
        report_id: str = Path(),
    ):
        is_loading = await self.redis_cache.get(report_id)

        if is_loading == b"1":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

        await self.redis_cache.set(report_id, b"1", 60 * 10)

        try:
            report = await self.report_repository.get_report_by_name(report_id)
            project, level = await self.report_repository.get_user_project_permission(report.project, user.sub)

            if level > 2:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to cancel project submission.",
                )

            tasks = await self.report_repository.get_tasks(
                0,
                1000,
                user.sub,
                project_id=report.project,
                start=report.start_date,
                end=report.end_date,
            )

            timesheets = await self.report_repository.get_timesheets(
                0,
                100,
                user.sub,
                project_id=report.project,
                start_date=report.start_date,
                end_date=report.end_date,
            )

            task_items = [
                task.model_dump(
                    include={
                        "subject",
                        "status",
                        "exp_start_date",
                        "expected_time",
                        "exp_end_date",
                        "progress",
                        "description",
                    }
                )
                for task in tasks.items
            ]
            timesheet_items = [
                timesheet.model_dump(
                    include={
                        "name",
                        "creation",
                        "start_date",
                        "end_date",
                        "total_hours",
                        "note",
                    }
                )
                for timesheet in timesheets.items
            ]

            response = await self.openai_client.responses.create(
                model="gpt-5-mini",
                instructions=report_summary_instruction,
                input=f"tasks={task_items}, timesheet={timesheet_items}",
                max_output_tokens=10000,
                top_p=1.0,
            )

            result = response.output_text
            report = await self.report_repository.update_report(report_id, summary=result)

            return ReportResponse.model_validate(
                {
                    "report": report,
                    "tasks": tasks.items,
                    "timesheets": timesheets.items,
                },
                from_attributes=True,
            )

        except Exception:
            pass

        finally:
            await self.redis_cache.delete(report_id)
