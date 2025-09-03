import datetime
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


class ProjectMethod(str, Enum):
    CODE = "code"
    NOCODE = "nocode"
    SHOP = "shop"


class NoCodePlatform(str, Enum):
    CAFE24 = "cafe24"
    GODO = "godo"
    SHOPIFY = "shopify"
    IMWEB = "imweb"
    FRAMER = "framer"
    WORDPRESS = "wordpress"
    WEBFLOW = "webflow"
    BUBBLE = "bubble"


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


class ERPNextProjectUserRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Project User")
    user: str
    welcome_email_sent: bool | None = Field(default=False)


class ERPNextTeam(BaseModel):
    member: str
    level: int


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
    customer: str | None = Field(None)

    custom_project_title: str | None = Field(default=None)
    custom_project_summary: str | None = Field(default=None)
    custom_project_status: CustomProjectStatus | None = Field(default=CustomProjectStatus.DRAFT)
    custom_ai_estimate: str | None = Field(default=None)
    custom_emoji: str | None = Field(default=None)
    custom_readiness_level: str | None = Field(default=None)  # ReadinessLevel Enum 사용 가능
    custom_content_pages: int | None = Field(default=None)
    custom_maintenance_required: bool | None = Field(default=False)

    custom_team: list[ERPNextTeam] | None = Field(default=None)
    custom_platforms: list[ERPNextProjectPlatformRow] | None = Field(default_factory=list)
    custom_features: list[ERPNextProjectFeatureRow] | None = Field(default_factory=list)
    custom_preferred_tech_stacks: list[ERPNextProjectPreferredTechStackRow] | None = Field(default_factory=list)
    custom_design_urls: list[ERPNextProjectDesignUrlRow] | None = Field(default_factory=list)
    custom_project_method: ProjectMethod | None = Field(default=None)
    custom_nocode_platform: NoCodePlatform | None = Field(default=None)

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

    @field_validator("custom_team", mode="before")
    @classmethod
    def parse_team(cls, v):
        if isinstance(v, str):
            try:
                team = [ERPNextTeam(**item) for item in json.loads(v)]
                return team
            except Exception as e:
                raise ValueError(f"Failed to parse team: {e}")
        return v


class ERPNextProjectForUser(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    creation: datetime.datetime | None = Field(default=None)
    modified: datetime.datetime | None = Field(default=None)

    project_name: str
    status: ERPNextProjectStatus | None = Field(default=ERPNextProjectStatus.OPEN)
    is_active: IsActive | None = Field(default=None)
    percent_complete: float | None = Field(default=None)
    custom_deletable: bool | None = Field(default=True)

    expected_start_date: datetime.date | None = Field(default=None)
    expected_end_date: datetime.date | None = Field(default=None)
    actual_start_date: datetime.date | None = Field(default=None)
    actual_end_date: datetime.date | None = Field(default=None)
    actual_time: float | None = Field(default=None)
    customer: str | None = Field(None)

    custom_project_title: str
    custom_project_summary: str
    custom_project_status: CustomProjectStatus | None = Field(default=CustomProjectStatus.DRAFT)
    custom_ai_estimate: str | None = Field(default=None)
    custom_emoji: str | None = Field(default=None)
    custom_readiness_level: str
    custom_content_pages: int | None = Field(default=None)
    custom_maintenance_required: bool | None = Field(default=False)

    custom_team: list[ERPNextTeam] | None = Field(default=None)
    custom_platforms: list[ERPNextProjectPlatformRow] | None = Field(default_factory=list)
    custom_features: list[ERPNextProjectFeatureRow] | None = Field(default_factory=list)
    custom_preferred_tech_stacks: list[ERPNextProjectPreferredTechStackRow] | None = Field(default_factory=list)
    custom_design_urls: list[ERPNextProjectDesignUrlRow] | None = Field(default_factory=list)
    custom_project_method: ProjectMethod | None = Field(default=None)
    custom_nocode_platform: NoCodePlatform | None = Field(default=None)

    estimated_costing: float | None = Field(default=None)

    @field_validator("custom_team", mode="before")
    @classmethod
    def parse_team(cls, v):
        if isinstance(v, str):
            try:
                team = [ERPNextTeam(**item) for item in json.loads(v)]
                return team
            except Exception as e:
                raise ValueError(f"Failed to parse team: {e}")
        return v


class OverviewERPNextProject(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    creation: datetime.datetime | None = Field(default=None)
    modified: datetime.datetime | None = Field(default=None)
    expected_start_date: datetime.date | None = Field(default=None)
    expected_end_date: datetime.date | None = Field(default=None)

    custom_team: list[ERPNextTeam] | None = Field(default=None)
    project_name: str
    custom_project_title: str
    custom_project_status: CustomProjectStatus | None = Field(default=CustomProjectStatus.DRAFT)


class CreateERPNextProject(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    custom_project_title: str
    custom_project_summary: str
    custom_readiness_level: str
    custom_project_method: ProjectMethod | None = Field(default=None)
    custom_nocode_platform: NoCodePlatform | None = Field(default=None)

    expected_start_date: datetime.date | None = Field(default=None)
    expected_end_date: datetime.date | None = Field(default=None)

    custom_content_pages: int | None = Field(default=None)
    custom_maintenance_required: bool | None = Field(default=False)

    custom_platforms: list[ERPNextProjectPlatformRow] = Field(default_factory=list)
    custom_features: list[ERPNextProjectFeatureRow] | None = Field(default_factory=list)
    custom_preferred_tech_stacks: list[ERPNextProjectPreferredTechStackRow] | None = Field(default_factory=list)
    custom_design_urls: list[ERPNextProjectDesignUrlRow] | None = Field(default_factory=list)


class UpdateERPNextProject(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    custom_project_title: str | None = Field(default=None)
    custom_project_summary: str | None = Field(default=None)
    custom_readiness_level: str | None = Field(default=None)
    custom_project_method: ProjectMethod | None = Field(default=None)
    custom_nocode_platform: NoCodePlatform | None = Field(default=None)
    custom_project_status: CustomProjectStatus | None = Field(default=CustomProjectStatus.DRAFT)

    is_active: IsActive | None = Field(default=None)

    expected_start_date: datetime.date | None = Field(default=None)
    expected_end_date: datetime.date | None = Field(default=None)
    customer: str | None = Field(None)

    custom_content_pages: int | None = Field(default=None)
    custom_maintenance_required: bool | None = Field(default=False)

    custom_platforms: list[ERPNextProjectPlatformRow] = Field(default_factory=list)
    custom_features: list[ERPNextProjectFeatureRow] | None = Field(default_factory=list)
    custom_preferred_tech_stacks: list[ERPNextProjectPreferredTechStackRow] | None = Field(default_factory=list)
    custom_design_urls: list[ERPNextProjectDesignUrlRow] | None = Field(default_factory=list)


class ERPNextProjectsRequest(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(10, ge=1, le=20, description="Page size")
    keyword: str | None = Field(default=None)
    order_by: str = Field(default="modified")
    status: str | None = Field(default=None)


class ProjectsPaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[ERPNextProjectForUser]


class OverviewProjectsPaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[OverviewERPNextProject]


class QuoteSlot(BaseModel):
    date: str
    remaining: str


class Quote(BaseModel):
    date: datetime.date | None = Field(default=None)
    inbound: bool | None = Field(default=False)


# --- Task Models ---


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


class ERPNextTaskDependsOnRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Task Depends On")
    task: str


class ERPNextTaskRequest(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)
    subject: str
    project: str | None = Field(default=None)
    depends_on: list[ERPNextTaskDependsOnRow] | None = Field(default_factory=list)


class ERPNextTasksRequest(BaseModel):
    page: int = Field(default=0)
    size: int = Field(default=20, ge=0, le=1000)
    order_by: list[str] | str | None = Field(default="modified")
    status: list[ERPNextTaskStatus] | ERPNextTaskStatus | None = Field(default=None)
    project_id: list[str] | str | None = Field(default=None)
    start: datetime.date | None = Field(default=None)
    end: datetime.date | None = Field(default=None)
    keyword: str | None = Field(default=None)


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
    model_config = ConfigDict(use_enum_values=True)
    name: str
    subject: str
    project: str

    color: str | None = Field(None)
    status: ERPNextTaskStatus | None = Field(None)

    parent_task: str | None = Field(None)
    exp_start_date: datetime.date | None = Field(None)
    expected_time: float | None = Field(default=0.0)
    exp_end_date: datetime.date | None = Field(None)
    progress: float = Field(0.0)

    description: str | None = Field(None)
    closing_date: datetime.date | None = Field(None)


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


# --- Timesheet ---


class TimeSheetRequest(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(40, ge=1, le=100, description="Page size")
    start_date: datetime.date
    end_date: datetime.date
    project_id: str


class TimeSheetStatus(str, Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    CANCELLED = "Cancelled"
    BILLED = "Billed"


class TimeSheetDocStatus(int, Enum):
    DRAFT = 0
    SUBMITTED = 1
    CANCELLED = 2


class ERPNextTimeSheet(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)

    # 기본 정보
    name: str
    owner: str
    creation: datetime.datetime
    modified: datetime.datetime
    modified_by: str
    docstatus: TimeSheetDocStatus = Field(default=TimeSheetDocStatus.DRAFT)
    idx: int
    title: str
    naming_series: str
    status: TimeSheetStatus = Field(default=TimeSheetStatus.DRAFT)

    # 연결 정보
    company: str | None = Field(default=None)
    customer: str | None = Field(default=None)
    sales_invoice: str | None = Field(default=None)
    salary_slip: str | None = Field(default=None)
    parent_project: str | None = Field(default=None)
    amended_from: str | None = Field(default=None)

    # 직원 정보
    employee: str | None = Field(default=None)
    employee_name: str | None = Field(default=None)
    department: str | None = Field(default=None)
    user: str | None = Field(default=None)

    # 날짜 및 시간
    start_date: datetime.date | None = Field(default=None)
    end_date: datetime.date | None = Field(default=None)
    total_hours: float | None = Field(default=None)
    total_billable_hours: float | None = Field(default=None)
    total_billed_hours: float | None = Field(default=None)

    # 금액 정보
    currency: str | None = Field(default=None)
    exchange_rate: float | None = Field(default=None)
    total_billable_amount: float | None = Field(default=None)
    total_billed_amount: float | None = Field(default=None)
    total_costing_amount: float | None = Field(default=None)
    base_total_billable_amount: float | None = Field(default=None)
    base_total_billed_amount: float | None = Field(default=None)
    base_total_costing_amount: float | None = Field(default=None)
    per_billed: float | None = Field(default=None)

    # 추가 정보
    note: str | None = Field(default=None)


class ERPNextTimeSheetForUser(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)

    # 기본 정보
    name: str
    creation: datetime.datetime
    modified: datetime.datetime
    idx: int
    title: str
    status: TimeSheetStatus = Field(default=TimeSheetStatus.DRAFT)

    # 연결 정보
    customer: str | None = Field(default=None)
    parent_project: str | None = Field(default=None)

    # 날짜 및 시간
    start_date: datetime.date | None = Field(default=None)
    end_date: datetime.date | None = Field(default=None)
    total_hours: float | None = Field(default=None)

    # 추가 정보
    note: str | None = Field(default=None)


class ERPNextTimeSheetForUserList(BaseModel):
    items: list[ERPNextTimeSheetForUser]


# --- Report Models ---


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


# --- Issue Models ---


class IssueType(str, Enum):
    design = "Design"
    feature = "Feature"
    etc = "ETC"


class ERPNextIssue(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str
    subject: str
    customer: str

    creation: datetime.datetime | None = Field(default=None)
    modified: datetime.datetime | None = Field(default=None)
    response_by: datetime.datetime | None = Field(default=None)
    sla_resolution_by: datetime.datetime | None = Field(default=None)
    first_response_time: float | None = Field(default=None)
    first_responded_on: datetime.datetime | None = Field(default=None)

    status: str | None = Field(default=None)
    priority: str | None = Field(default=None)
    issue_type: IssueType | None = Field(default=None)
    description: str | None = Field(default=None)
    on_hold_since: datetime.datetime | None = Field(default=None)
    total_hold_time: float | None = Field(default=None)
    avg_response_time: float | None = Field(default=None)

    project: str | None = Field(default=None)
    company: str | None = Field(default=None)


class ERPNextIssuesRequest(BaseModel):
    page: int = Field(default=0)
    size: int = Field(default=20, ge=0, le=1000)
    order_by: list[str] | str | None = Field(default="modified desc")
    issue_type: list[IssueType] | IssueType | None = Field(default=None)
    project_id: list[str] | str | None = Field(default=None)
    start: datetime.date | None = Field(default=None)
    end: datetime.date | None = Field(default=None)
    keyword: str | None = Field(default=None)
    status: list[str] | str | None = Field(default=None)


class CreateERPNextIssue(BaseModel):
    subject: str
    project: str | None = Field(default=None)

    priority: str | None = Field(default=None)
    issue_type: IssueType | None = Field(default=None)
    description: str | None = Field(default=None)


class UpdateERPNextIssue(BaseModel):
    subject: str | None = Field(default=None)

    priority: str | None = Field(default=None)
    issue_type: IssueType | None = Field(default=None)
    description: str | None = Field(default=None)

    project: str | None = Field(default=None)


class ERPNextIssuePaginatedResponse(BaseModel):
    items: list[ERPNextIssue]


# --- Contract Model ---


class ERPNextContract(BaseModel):
    name: str
    owner: str
    custom_name: str
    creation: datetime.datetime
    modified: datetime.datetime
    modified_by: str
    docstatus: int
    idx: int
    party_type: str | None = Field(default=None)
    is_signed: bool | None = Field(default=None)
    custom_subscribe: bool | None = Field(default=None)
    party_name: str | None = Field(default=None)
    party_user: str | None = Field(default=None)
    status: str | None = Field(default=None)
    fulfilment_status: str | None = Field(default=None)
    party_full_name: str | None = Field(default=None)
    start_date: datetime.date | None = Field(default=None)
    end_date: datetime.date | None = Field(default=None)
    custom_customer_sign: str | None = Field(default=None)
    custom_fee: int | None = Field(default=None)
    custom_down_payment: float | None = Field(default=None)
    custom_balance: float | None = Field(default=None)
    custom_maintenance: int | None = Field(default=None)
    signee: str | None = Field(default=None)
    signed_on: datetime.datetime | None = Field(default=None)
    ip_address: str | None = Field(default=None)
    contract_template: str | None = Field(default=None)
    contract_terms: str | None = Field(default=None)
    requires_fulfilment: int | None = Field(default=None)
    fulfilment_deadline: datetime.datetime | None = Field(default=None)
    signee_company: str | None = Field(default=None)
    signed_by_company: str | None = Field(default=None)
    document_type: str | None = Field(default=None)
    document_name: str | None = Field(default=None)
    amended_from: str | None = Field(default=None)


class UserERPNextContract(BaseModel):
    name: str
    owner: str
    custom_name: str
    creation: datetime.datetime
    modified: datetime.datetime
    modified_by: str
    docstatus: int
    idx: int
    is_signed: bool | None = Field(default=None)
    custom_subscribe: bool | None = Field(default=None)
    party_name: str | None = Field(default=None)
    status: str | None = Field(default=None)
    start_date: datetime.date | None = Field(default=None)
    end_date: datetime.date | None = Field(default=None)
    custom_customer_sign: str | None = Field(default=None)
    custom_fee: int | None = Field(default=None)
    custom_down_payment: float | None = Field(default=None)
    custom_balance: float | None = Field(default=None)
    custom_maintenance: int | None = Field(default=None)
    signee: str | None = Field(default=None)
    signed_on: datetime.datetime | None = Field(default=None)
    ip_address: str | None = Field(default=None)
    contract_template: str | None = Field(default=None)
    contract_terms: str | None = Field(default=None)
    document_type: str | None = Field(default=None)
    document_name: str | None = Field(default=None)


class UpdateERPNextContract(BaseModel):
    ip_address: str | None = Field(default=None)
    is_signed: bool | None = Field(default=None)
    custom_customer_sign: str | None = Field(default=None)


class ERPNextContractRequest(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(10, ge=1, le=20, description="Page size")
    project_id: list[str] | str | None = Field(default=None)
    keyword: str | None = Field(default=None)
    order_by: list[str] | str = Field(default="modified")
    status: list[str] | str | None = Field(default=None)
    start: datetime.date | None = Field(default=None)
    end: datetime.date | None = Field(default=None)


class ERPNextContractPaginatedResponse(BaseModel):
    items: list[UserERPNextContract]


# --- ETC Models ---


class ERPNextFile(BaseModel):
    model_config = ConfigDict(extra="allow")
    doctype: str | None = Field(default="Files")

    creation: datetime.datetime | None = Field(default=None)
    modified: datetime.datetime | None = Field(default=None)

    file_name: str
    key: str
    uploader: str
    algorithm: str = Field(default="AES256")
    sse_key: str | None = Field(default=None)

    project: str | None = Field(default=None)
    task: str | None = Field(default=None)
    issue: str | None = Field(default=None)


class ERPNextFileRequest(BaseModel):
    page: int = Field(default=0, ge=0)
    size: int = Field(default=20, ge=0, le=100)
    order_by: str = Field(default="modified")

    task: str | None = Field(default=None)
    issue: str | None = Field(default=None)


class ERPNextFilesResponse(BaseModel):
    items: list[ERPNextFile]


class ProjectSummary2InfoResponse(BaseModel):
    custom_project_title: str
    custom_readiness_level: str
    custom_platforms: list[Platform] = Field(default_factory=list)
    custom_project_method: ProjectMethod | None = Field(default=None)
    custom_nocode_platform: NoCodePlatform | None = Field(default=None)


class ProjectFeatureEstimateRequest(BaseModel):
    project_name: str
    project_summary: str
    readiness_level: ReadinessLevel
    platforms: list[Platform]
    project_method: ProjectMethod | None = Field(default=None)
    nocode_platform: NoCodePlatform | None = Field(default=None)


class ProjectFeatureEstimateResponse(BaseModel):
    feature_list: list[str]
