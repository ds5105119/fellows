from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, conint


class ReadinessLevel(str, Enum):
    idea = "idea"
    requirements = "requirements"
    wireframe = "wireframe"


class ComplexityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class DesignComplexity(str, Enum):
    basic = "basic"
    custom = "custom"


class Platform(str, Enum):
    web = "web"
    android = "android"
    ios = "ios"


class ProjectEstimateRequest(BaseModel):
    project_name: str = Field(..., description="프로젝트명")  # ✅ 필수
    project_summary: str = Field(..., description="한 줄 설명")  # ✅ 필수
    platforms: List[Platform] = Field(..., description="지원 플랫폼")  # ✅ 필수
    readiness_level: ReadinessLevel = Field(..., description="사전 준비도")  # ✅ 필수

    feature_list: Optional[List[str]] = Field(None, description="주요 기능 키 (e.g. login, payment)")
    design_complexity: Optional[DesignComplexity] = Field(None, description="디자인 난이도")
    reference_urls: Optional[List[HttpUrl]] = Field(default=None, description="참고 사이트 URL 목록")
    desired_deadline: Optional[date] = Field(None, description="희망 완료일")

    # 추가 필드는 그대로 유지
    admin_panel_required: bool = Field(False, description="관리자 페이지 필요 여부")
    third_party_integrations: List[str] = Field([], description="연동할 외부 시스템/서비스 목록")
    multi_language_support: bool = Field(False, description="다국어 지원 여부")
    maintenance_required: bool = Field(False, description="출시 후 유지보수 필요 여부")
    expected_monthly_users: Optional[conint(ge=0)] = Field(None, description="예상 월간 활성 사용자 수")
    security_compliance: List[str] = Field([], description="준수해야 할 보안/컴플라이언스 기준 목록")
    analytics_required: bool = Field(False, description="분석·로그 수집 필요 여부")
    content_pages: Optional[conint(ge=0)] = Field(None, description="웹 콘텐츠 페이지 수")
