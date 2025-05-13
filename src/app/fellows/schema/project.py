from datetime import date, datetime
from enum import Enum

from pydantic import AnyUrl, BaseModel, ConfigDict, Field

from src.app.user.schema.cloud import FileRecordResponseOnly


class Platform(str, Enum):
    web = "web"
    android = "android"
    ios = "ios"


class ReadinessLevel(str, Enum):
    idea = "idea"
    requirements = "requirements"
    wireframe = "wireframe"


class ProjectFeatureEstimateRequest(BaseModel):
    project_name: str
    project_summary: str
    readiness_level: ReadinessLevel


class ProjectFeatureEstimateResponse(BaseModel):
    feature_list: list[str]


class ProjectGroupsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    group_id: str


class ProjectFileRecordsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_info_id: int | None = Field(default=None)
    file_record_key: str
    file_record: FileRecordResponseOnly | None = Field(default=None)


class ProjectInfoSchema(BaseModel):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

    # 필수 항목
    project_name: str
    project_summary: str
    platforms: list[Platform]
    readiness_level: ReadinessLevel

    # --- 기능 요구사항 ---
    feature_list: list[str] | None = Field(default=None)
    content_pages: int | None = Field(default=None, ge=0)
    preferred_tech_stack: list[str] | None = Field(default=None)

    # --- 디자인 요구사항 ---
    design_requirements: str | None = Field(default=None)
    reference_design_url: list[AnyUrl] | None = Field(default=None)
    files: list[ProjectFileRecordsSchema] = Field(default_factory=list)

    # --- 일정 및 기타 ---
    start_date: date | None = Field(default_factory=date.today)
    desired_deadline: date | None = Field(default=None)
    maintenance_required: bool = Field(False)


class GetProjectsRequest(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(10, ge=1, le=20, description="Page size")
    keyword: str | None = Field(default=None)
    order_by: str = Field(default="updated_at")


class ProjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sub: str
    project_id: str
    status: str
    ai_estimate: str | None = None
    created_at: datetime
    updated_at: datetime
    deletable: bool

    project_info: ProjectInfoSchema
    group_links: list[ProjectGroupsSchema] = Field(default_factory=list)
