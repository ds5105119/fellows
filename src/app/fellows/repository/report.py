import datetime

from src.app.fellows.repository.frappe import FrappReadRepository
from src.app.fellows.schema.report import (
    ERPNextReport,
)
from src.core.utils.frappeclient import AsyncFrappeClient


class ReportCreateRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client

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


class ReportReadRepository(FrappReadRepository):
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


class ReportUpdateRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client

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


class ReportDeleteRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client


class ReportRepository(
    ReportCreateRepository,
    ReportReadRepository,
    ReportUpdateRepository,
    ReportDeleteRepository,
):
    pass
