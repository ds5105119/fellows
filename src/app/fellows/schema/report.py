import datetime

from pydantic import BaseModel, ConfigDict

from src.app.fellows.schema.project import ERPNextTaskForUser, ERPNextTimeSheetForUser


class DailyReportRequest(BaseModel):
    date: datetime.date


class MonthlyReportRequest(BaseModel):
    date: datetime.date


class ERPNextReport(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)

    name: str
    creation: datetime.datetime
    modified: datetime.datetime

    project: str
    start_date: datetime.date
    end_date: datetime.date

    summary: str | None = None


class ReportResponse(BaseModel):
    report: ERPNextReport
    tasks: list[ERPNextTaskForUser]
    timesheets: list[ERPNextTimeSheetForUser]
