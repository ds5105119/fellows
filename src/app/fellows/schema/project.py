from datetime import date, datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class Platform(str, Enum):
    web = "web"
    android = "android"
    ios = "ios"


class ReadinessLevel(str, Enum):
    idea = "idea"
    requirements = "requirements"
    wireframe = "wireframe"


class ProjectInfoSchema(BaseModel):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)

    # 필수 항목
    project_name: str = Field(description="프로젝트 이름 (예: 'ABC 쇼핑몰 구축')")
    project_summary: str = Field(description="프로젝트의 주요 목표 및 기능에 대한 간략한 설명 (2-3 문장)")
    platforms: List[Platform] = Field(description="개발 대상 플랫폼")
    readiness_level: ReadinessLevel = Field(..., description="사전 준비도")

    # --- 디자인 요구사항 ---
    design_requirements: str | None = Field(
        None,
        description="디자인 관련 구체적인 요구사항 (예: '제공된 Figma 시안 기반 개발', '애니메이션 효과 중요', '브랜드 가이드라인 준수')",
    )

    # --- 기능 요구사항 (선택적이지만 구체적일수록 좋음) ---
    feature_list: List[str] | None = Field(
        None,
        description="구현해야 할 주요 기능 키워드 목록 (예: 실시간 채팅, 대시보드, 푸시 메시지, 알림톡, PG 연동(토스 등), AWS, GA, 로그 등)",
    )
    i18n_support: bool = Field(False, description="다국어 지원 필요 여부")
    content_pages: int | None = Field(None, ge=0, description="단순 콘텐츠 페이지 예상 개수")

    # --- 기술 및 환경 (선택적 정보) ---
    preferred_tech_stack: List[str] | None = Field(
        None, description="선호하는 기술 스택 목록 (예: ['React', 'Node.js', 'PostgreSQL', 'AWS'])"
    )
    security_compliance: List[str] = Field(
        default_factory=list,
        description="반드시 준수해야 할 보안 표준 또는 컴플라이언스 목록 (예: 'ISMS', '개인정보보호법')",
    )

    # --- 일정 및 기타 ---
    start_date: date | None = Field(default_factory=date.today, description="희망 시작일 (YYYY-MM-DD)")
    desired_deadline: date | None = Field(default=None, description="희망 완료일 (YYYY-MM-DD)")
    maintenance_required: bool = Field(False, description="출시 후 별도의 기술 지원 또는 유지보수 계약 필요 여부")


class GetProjectsRequest(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(10, ge=1, le=20, description="Page size")
    keyword: str | None = Field(default=None)
    order_by: str = Field(default="updated_at")


class ProjectGroupLinkSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group_id: str


class ProjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sub: str
    project_id: str
    status: str
    ai_estimate: str | None = None
    created_at: datetime
    updated_at: datetime

    project_info: ProjectInfoSchema
    group_links: List[ProjectGroupLinkSchema] = Field(default_factory=list)
