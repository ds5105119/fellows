from datetime import date, datetime
from enum import Enum

from pydantic import AliasChoices, AnyUrl, BaseModel, ConfigDict, Field, field_serializer

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
    platforms: list[Platform]


class ProjectFeatureEstimateResponse(BaseModel):
    feature_list: list[str]


class ProjectGroupsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    group_id: str


class ProjectFileRecordsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_info_id: int | None = Field(default=None)
    file_record_key: str
    file_record: FileRecordResponseOnly


class ProjectTaskRequest(BaseModel):
    page: int = Field(default=0, ge=0)
    size: int = Field(default=20, ge=0, le=100)


class ProjectInfoSchema(BaseModel):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True, extra="allow")

    # 필수 항목
    project_name: str = Field(
        serialization_alias="custom_project_title",
        validation_alias=AliasChoices("project_name", "custom_project_title"),
    )
    project_summary: str = Field(
        serialization_alias="custom_project_summary",
        validation_alias=AliasChoices("project_summary", "custom_project_summary"),
    )
    platforms: list[Platform] = Field(
        default_factory=list,
        serialization_alias="custom_platforms",
        validation_alias=AliasChoices("platforms", "custom_platforms"),
    )
    readiness_level: ReadinessLevel = Field(
        serialization_alias="custom_readiness_level",
        validation_alias=AliasChoices("readiness_level", "custom_readiness_level"),
    )

    # --- 기능 요구사항 ---
    feature_list: list[str] = Field(
        default_factory=list,
        serialization_alias="custom_features",
        validation_alias=AliasChoices("feature_list", "custom_features"),
    )
    content_pages: int | None = Field(
        default=None,
        ge=0,
        serialization_alias="custom_content_pages",
        validation_alias=AliasChoices("content_pages", "custom_content_pages"),
    )
    preferred_tech_stack: list[str] = Field(
        default_factory=list,
        serialization_alias="custom_preferred_tech_stacks",
        validation_alias=AliasChoices("preferred_tech_stack", "custom_preferred_tech_stacks"),
    )

    # --- 디자인 요구사항 ---
    design_requirements: str | None = Field(
        default=None,
        serialization_alias="custom_design_requirements",
        validation_alias=AliasChoices("design_requirements", "custom_design_requirements"),
    )
    reference_design_url: list[AnyUrl] = Field(
        default_factory=list,
        serialization_alias="custom_design_urls",
        validation_alias=AliasChoices("reference_design_url", "custom_design_urls"),
    )
    files: list[str] = Field(
        default_factory=list,
        serialization_alias="custom_files",
        validation_alias=AliasChoices("files", "custom_files"),
    )

    # --- 일정 및 기타 ---
    start_date: date | None = Field(
        default=None,
        serialization_alias="expected_start_date",
        validation_alias=AliasChoices("start_date", "expected_start_date"),
    )
    desired_deadline: date | None = Field(
        default=None,
        serialization_alias="expected_end_date",
        validation_alias=AliasChoices("desired_deadline", "expected_end_date"),
    )
    maintenance_required: bool = Field(
        False,
        serialization_alias="custom_maintenance_required",
        validation_alias=AliasChoices("maintenance_required", "custom_maintenance_required"),
    )

    @field_serializer("platforms")
    def serialize_platforms(self, platforms: list[Platform], _info):
        return [{"doctype": "Platforms", "platform": platform} for platform in platforms]

    @field_serializer("feature_list")
    def serialize_feature_list(self, feature_list: list[str], _info):
        return [{"doctype": "Features", "feature": feature} for feature in feature_list]

    @field_serializer("preferred_tech_stack")
    def serialize_preferred_tech_stack(self, preferred_tech_stack: list[str], _info):
        return [{"doctype": "Preferred Tech Stack", "stack": stack} for stack in preferred_tech_stack]

    @field_serializer("reference_design_url")
    def serialize_reference_design_url(self, reference_design_url: list[AnyUrl], _info):
        return [{"doctype": "Project Design Url", "url": url} for url in reference_design_url]

    @field_serializer("files")
    def serialize_files(self, files: list[str], _info):
        return []


class ProjectSchema(ProjectInfoSchema):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True, extra="allow")

    sub: str = Field(
        serialization_alias="custom_sub",
        validation_alias=AliasChoices("sub", "custom_sub"),
    )
    project_id: str = Field(
        serialization_alias="project_name",
        validation_alias=AliasChoices("project_id", "project_name"),
    )
    deletable: bool = Field(
        serialization_alias="custom_deletable",
        validation_alias=AliasChoices("deletable", "custom_deletable"),
    )

    status: str = Field(
        serialization_alias="custom_project_status",
        validation_alias=AliasChoices("status", "custom_project_status"),
    )
    ai_estimate: str | None = Field(
        default=None,
        serialization_alias="custom_ai_estimate",
        validation_alias=AliasChoices("ai_estimate", "custom_ai_estimate"),
    )
    emoji: str | None = Field(
        default=None,
        serialization_alias="custom_emoji",
        validation_alias=AliasChoices("emoji", "custom_emoji"),
    )
    total_amount: int | None = Field(
        default=None,
        serialization_alias="estimated_costing",
        validation_alias=AliasChoices("total_amount", "estimated_costing"),
    )
