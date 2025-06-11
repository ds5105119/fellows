import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer

# --- Enums ---


class Platform(str, Enum):
    WEB = "web"
    ANDROID = "android"
    IOS = "ios"


class ReadinessLevel(str, Enum):
    IDEA = "idea"
    REQUIREMENTS = "requirements"
    WIREFRAME = "wireframe"


class ERPNextProjectStatus(str, Enum):
    OPEN = "Open"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class CustomProjectStatus(str, Enum):
    DRAFT = "draft"
    PROCESS_1 = "process:1"
    PROCESS_2 = "process:2"
    COMPLETE = "complete"
    MAINTENANCE = "maintenance"


class IsActive(str, Enum):
    YES = "Yes"
    NO = "No"


class PercentCompleteMethod(str, Enum):
    MANUAL = "Manual"
    TASK_COMPLETION = "Task Completion"
    TASK_PROGRESS = "Task Progress"
    TASK_WEIGHT = "Task Weight"


class Priority(str, Enum):
    MEDIUM = "Medium"
    LOW = "Low"
    HIGH = "High"


class ERPNextTaskStatus(str, Enum):
    OPEN = "Open"
    WORKING = "Working"
    PENDING_REVIEW = "Pending Review"
    OVERDUE = "Overdue"
    TEMPLATE = "Template"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ERPNextTaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class ERPNextToDoStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"


class ERPNextToDoPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# --- Child Table Models for ERPNext ---


class ERPNextProjectPlatformRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Platforms")
    platform: str


class ERPNextProjectFeatureRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Features")
    feature: str


class ERPNextProjectPreferredTechStackRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Preferred Tech Stack")
    stack: str


class ERPNextProjectDesignUrlRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Project Design Url")
    url: str


class ERPNextProjectFileRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Files")

    creation: datetime.datetime | None = Field(default=None)
    modified: datetime.datetime | None = Field(default=None)

    file_name: str
    key: str
    uploader: str
    algorithm: str = Field(default="AES256")
    sse_key: str | None = Field(default=None)


class ERPNextProjectUserRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Project User")
    user: str
    welcome_email_sent: bool | None = Field(default=False)


# --- Main Project Model (CSV 기반 업데이트) ---


class ERPNextProject(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)

    creation: datetime.datetime | None = Field(default=None)
    modified: datetime.datetime | None = Field(default=None)

    naming_series: str = Field(default="PROJ-.####")
    project_name: str
    status: ERPNextProjectStatus | None = Field(default=ERPNextProjectStatus.OPEN)
    project_type: str | None = Field(default=None)
    is_active: IsActive | None = Field(default=None)
    percent_complete_method: PercentCompleteMethod | None = Field(default=PercentCompleteMethod.TASK_COMPLETION)
    percent_complete: float | None = Field(default=None)
    custom_deletable: bool | None = Field(default=True)

    project_template: str | None = Field(default=None)
    expected_start_date: datetime.date | None = Field(default=None)
    expected_end_date: datetime.date | None = Field(default=None)
    actual_start_date: datetime.date | None = Field(default=None)
    actual_end_date: datetime.date | None = Field(default=None)
    actual_time: float | None = Field(default=None)

    priority: Priority | None = Field(default=None)
    department: str | None = Field(default=None)

    custom_project_title: str | None = Field(default=None)
    custom_project_summary: str | None = Field(default=None)
    custom_project_status: CustomProjectStatus | None = Field(default=CustomProjectStatus.DRAFT)
    custom_ai_estimate: str | None = Field(default=None)
    custom_emoji: str | None = Field(default=None)
    custom_readiness_level: str | None = Field(default=None)  # ReadinessLevel Enum 사용 가능
    custom_content_pages: int | None = Field(default=None)
    custom_maintenance_required: bool | None = Field(default=False)

    custom_sub: str | None = Field(default=None)
    custom_platforms: list[ERPNextProjectPlatformRow] | None = Field(default_factory=list)
    custom_files: list[ERPNextProjectFileRow] | None = Field(default_factory=list)
    custom_features: list[ERPNextProjectFeatureRow] | None = Field(default_factory=list)
    custom_preferred_tech_stacks: list[ERPNextProjectPreferredTechStackRow] | None = Field(default_factory=list)
    custom_design_urls: list[ERPNextProjectDesignUrlRow] | None = Field(default_factory=list)

    estimated_costing: float | None = Field(default=None)
    total_costing_amount: float | None = Field(default=None)
    total_expense_claim: float | None = Field(default=None)
    total_purchase_cost: float | None = Field(default=None)
    company: str = Field(default="Fellows")
    cost_center: str | None = Field(default=None)

    total_sales_amount: float | None = Field(default=None)
    total_billable_amount: float | None = Field(default=None)
    total_billed_amount: float | None = Field(default=None)
    total_consumed_material_cost: float | None = Field(default=None)

    gross_margin: float | None = Field(default=None)
    per_gross_margin: float | None = Field(default=None)

    users: list[ERPNextProjectUserRow] | None = Field(default_factory=list)

    @field_serializer("users", when_used="json-unless-none")
    def serialize_users(self, users_list: list[ERPNextProjectUserRow] | None, _info):
        if users_list is None:
            return None
        return [user.model_dump(exclude_none=True) for user in users_list]

    @field_serializer("custom_platforms", when_used="json-unless-none")
    def serialize_custom_platforms(self, platforms_list: list[ERPNextProjectPlatformRow] | None, _info):
        if platforms_list is None:
            return None
        return [platform.model_dump(exclude_none=True) for platform in platforms_list]

    @field_serializer("custom_files", when_used="json-unless-none")
    def serialize_custom_files(self, files_list: list[ERPNextProjectFileRow] | None, _info):
        if files_list is None:
            return None
        return [file_item.model_dump(exclude_none=True) for file_item in files_list]

    @field_serializer("custom_features", when_used="json-unless-none")
    def serialize_custom_features(self, features_list: list[ERPNextProjectFeatureRow] | None, _info):
        if features_list is None:
            return None
        return [feature.model_dump(exclude_none=True) for feature in features_list]

    @field_serializer("custom_preferred_tech_stacks", when_used="json-unless-none")
    def serialize_custom_preferred_tech_stacks(
        self, stacks_list: list[ERPNextProjectPreferredTechStackRow] | None, _info
    ):
        if stacks_list is None:
            return None
        return [stack.model_dump(exclude_none=True) for stack in stacks_list]

    @field_serializer("custom_design_urls", when_used="json-unless-none")
    def serialize_custom_design_urls(self, urls_list: list[ERPNextProjectDesignUrlRow] | None, _info):
        if urls_list is None:
            return None
        return [url_item.model_dump(exclude_none=True, by_alias=False) for url_item in urls_list]


class UserERPNextProject(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)
    custom_project_title: str
    custom_project_summary: str
    custom_readiness_level: str

    expected_start_date: datetime.date | None = Field(default=None)
    expected_end_date: datetime.date | None = Field(default=None)

    custom_content_pages: int | None = Field(default=None)
    custom_maintenance_required: bool | None = Field(default=False)

    custom_platforms: list[ERPNextProjectPlatformRow] = Field(default_factory=list)
    custom_files: list[ERPNextProjectFileRow] | None = Field(default_factory=list)
    custom_features: list[ERPNextProjectFeatureRow] | None = Field(default_factory=list)
    custom_preferred_tech_stacks: list[ERPNextProjectPreferredTechStackRow] | None = Field(default_factory=list)
    custom_design_urls: list[ERPNextProjectDesignUrlRow] | None = Field(default_factory=list)

    @field_serializer("custom_platforms", when_used="json-unless-none")
    def serialize_custom_platforms(self, platforms_list: list[ERPNextProjectPlatformRow] | None, _info):
        if platforms_list is None:
            return None
        return [platform.model_dump(exclude_none=True) for platform in platforms_list]

    @field_serializer("custom_files", when_used="json-unless-none")
    def serialize_custom_files(self, files_list: list[ERPNextProjectFileRow] | None, _info):
        if files_list is None:
            return None
        return [file_item.model_dump(exclude_none=True) for file_item in files_list]

    @field_serializer("custom_features", when_used="json-unless-none")
    def serialize_custom_features(self, features_list: list[ERPNextProjectFeatureRow] | None, _info):
        if features_list is None:
            return None
        return [feature.model_dump(exclude_none=True) for feature in features_list]

    @field_serializer("custom_preferred_tech_stacks", when_used="json-unless-none")
    def serialize_custom_preferred_tech_stacks(
        self, stacks_list: list[ERPNextProjectPreferredTechStackRow] | None, _info
    ):
        if stacks_list is None:
            return None
        return [stack.model_dump(exclude_none=True) for stack in stacks_list]

    @field_serializer("custom_design_urls", when_used="json-unless-none")
    def serialize_custom_design_urls(self, urls_list: list[ERPNextProjectDesignUrlRow] | None, _info):
        if urls_list is None:
            return None
        return [url_item.model_dump(exclude_none=True, by_alias=False) for url_item in urls_list]


class ERPNextProjectsRequest(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(10, ge=1, le=20, description="Page size")
    keyword: str | None = Field(default=None)
    order_by: str = Field(default="modified")
    status: str | None = Field(default=None)


class ProjectsPaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[ERPNextProject]


# --- Task Models ---


class ERPNextTaskDependsOnRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Task Depends On")
    task: str


class ERPNextTaskRequest(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)
    subject: str
    project: str | None = Field(default=None)
    depends_on: list[ERPNextTaskDependsOnRow] | None = Field(default_factory=list)

    @field_serializer("depends_on", when_used="json-unless-none")
    def serialize_depends_on(self, depends_on_list: list[ERPNextTaskDependsOnRow] | None, _info):
        if depends_on_list is None:
            return None
        return [item.model_dump(exclude_none=True) for item in depends_on_list]


class ERPNextTask(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)
    subject: str
    project: str
    issue: str | None = Field(None)
    type: str | None = Field(None)
    color: str | None = Field(None)
    is_group: bool = Field(default=False)
    is_template: bool = Field(default=False)
    custom_is_user_visible: bool = Field(default=False)
    custom_sub: str | None = Field(default=None)

    status: ERPNextTaskStatus | None = Field(None)
    priority: ERPNextTaskPriority | None = Field(None)
    task_weight: float | None = Field(None)
    parent_task: str | None = Field(None)
    completed_by: str | None = Field(None)
    completed_on: datetime.date | None = Field(None)

    exp_start_date: datetime.date | None = Field(None)
    expected_time: float | None = Field(default=0.0)
    start: int | None = Field(None)

    exp_end_date: datetime.date | None = Field(None)
    progress: float | None = Field(None)
    duration: int | None = Field(None)
    is_milestone: bool = Field(default=False)

    description: str | None = Field(None)

    depends_on: list[ERPNextTaskDependsOnRow] | None = Field(default_factory=list)

    review_date: datetime.date | None = Field(None)
    closing_date: datetime.date | None = Field(None)

    department: str | None = Field(None)
    company: str | None = Field(None)


class ERPNextTaskForUser(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)
    subject: str
    project: str
    color: str | None = Field(None)
    status: ERPNextTaskStatus | None = Field(None)

    exp_start_date: datetime.date | None = Field(None)
    expected_time: float | None = Field(default=0.0)
    exp_end_date: datetime.date | None = Field(None)
    progress: float = Field(0.0)

    description: str | None = Field(None)
    closing_date: datetime.date | None = Field(None)


class ProjectTaskRequest(BaseModel):
    page: int = Field(default=0, ge=0)
    size: int = Field(default=20, ge=0, le=100)


class ERPNextTaskPaginatedResponse(BaseModel):
    items: list[ERPNextTaskForUser]


class ERPNextToDo(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)
    status: ERPNextToDoStatus = Field(default=ERPNextToDoStatus.OPEN)
    priority: ERPNextToDoPriority = Field(default=ERPNextToDoPriority.MEDIUM)
    color: str | None = Field(default=None)
    date: datetime.date | None = Field(default=None)
    allocated_to: str | None = Field(default=None)
    description: str
    reference_type: str | None = Field(default=None)
    reference_name: str | None = Field(default=None)
    role: str | None = Field(default=None)
    assigned_by: str | None = Field(default=None)


class ProjectFeatureEstimateRequest(BaseModel):
    project_name: str
    project_summary: str
    readiness_level: ReadinessLevel
    platforms: list[Platform]


class ProjectFeatureEstimateResponse(BaseModel):
    feature_list: list[str]
