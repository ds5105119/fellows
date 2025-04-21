import polars as pl
from sqlalchemy import Boolean, DateTime, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base
from src.core.utils.openapi.data_helper import cast_y_null_to_bool, join
from src.core.utils.openapi.data_saver import PostgresDataSaver

columns_mapping = {
    "등록일시": "created_at",
    "수정일시": "updated_at",
    "사용자구분": "user_type",
    "서비스ID": "service_id",
    "서비스명": "service_name",
    "서비스목적요약": "service_summary",
    "서비스분야": "service_category",
    "선정기준": "service_conditions",
    "서비스목적": "service_description",
    "부서명": "offc_name",
    "소관기관명": "dept_name",
    "소관기관유형": "dept_type",
    "소관기관코드": "dept_code",
    "조회수": "views",
    "신청기한": "apply_period",
    "신청방법": "apply_method",
    "온라인신청사이트URL": "apply_url",
    "접수기관": "receiving_agency",
    "지원내용": "support_details",
    "지원대상": "support_targets",
    "지원유형": "support_type",
    "구비서류": "document",
    "상세조회URL": "detail_url",
    "전화문의": "contact",
    "법령": "law",
}


class GovWelfareSaver(PostgresDataSaver):
    def build(self):
        path_order = {"/gov24/v3/serviceList": 1, "/gov24/v3/serviceDetail": 2, "/gov24/v3/supportConditions": 3}
        self.manager = tuple(sorted(self.manager, key=lambda manager: path_order.get(manager.path, float("inf"))))

        df = join(*[m.data for m in self.manager], by=["서비스ID"]).sort("서비스ID")
        df = df.rename(columns_mapping)
        df = df.drop(["자치법규", "행정규칙", "문의처", "접수기관명"], strict=False)
        df = df.filter(df["user_type"].str.contains("개인") | df["user_type"].str.contains("가구"))
        df = cast_y_null_to_bool(df)
        df = df.with_columns(pl.col("views").fill_null("0").cast(pl.Int32))
        df = df.with_columns(
            pl.col("created_at").str.strptime(dtype=pl.Datetime, format="%Y%m%d%H%M%S").alias("created_at"),
            pl.col("updated_at").str.strptime(dtype=pl.Datetime, format="%Y%m%d%H%M%S").alias("updated_at"),
        )
        df = df.sort(by=["updated_at", "service_id"], descending=[True, False], maintain_order=True)

        return df


class GovWelfare(Base):
    __tablename__ = "gov_welfare"
    __table_args__ = (
        Index(
            "ix_for_overcome",
            *("JA0201", "JA0202", "JA0203", "JA0204", "JA0205"),
        ),
        Index(
            "ix_for_life",
            *("JA0301", "JA0302", "JA0303"),
        ),
        Index(
            "ix_for_primary_industry",
            *("JA0313", "JA0314", "JA0315", "JA0316"),
        ),
        Index(
            "ix_for_education",
            *("JA0317", "JA0318", "JA0319", "JA0320", "JA0322"),
        ),
        Index(
            "ix_for_family",
            *("JA0401", "JA0402", "JA0403", "JA0404", "JA0410", "JA0411", "JA0412", "JA0413", "JA0414"),
        ),
        Index(
            "ix_for_business",
            *("JA1101", "JA1102", "JA1103", "JA1201", "JA1202", "JA1299"),
        ),
        Index(
            "ix_for_organization",
            *("JA2101", "JA2102", "JA2103", "JA2201", "JA2202", "JA2203", "JA2299"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[str] = mapped_column(DateTime, nullable=True)
    views: Mapped[int] = mapped_column(Integer, nullable=True, index=True)

    user_type: Mapped[str] = mapped_column(Text, nullable=True)

    service_id: Mapped[int] = mapped_column(Text, nullable=True)
    service_name: Mapped[str] = mapped_column(Text, nullable=True)
    service_summary: Mapped[str] = mapped_column(Text, nullable=True)
    service_category: Mapped[int] = mapped_column(Text, nullable=True)
    service_conditions: Mapped[str] = mapped_column(Text, nullable=True)
    service_description: Mapped[str] = mapped_column(Text, nullable=True)

    offc_name: Mapped[str] = mapped_column(Text, nullable=True)
    dept_name: Mapped[str] = mapped_column(Text, nullable=True)
    dept_type: Mapped[str] = mapped_column(Text, nullable=True, index=True)
    dept_code: Mapped[str] = mapped_column(Text, nullable=True)

    apply_period: Mapped[str] = mapped_column(Text, nullable=True)
    apply_method: Mapped[str] = mapped_column(Text, nullable=True)
    apply_url: Mapped[str] = mapped_column(Text, nullable=True)
    document: Mapped[str] = mapped_column(Text, nullable=True)
    receiving_agency: Mapped[str] = mapped_column(Text, nullable=True)
    contact: Mapped[str] = mapped_column(Text, nullable=True)

    support_details: Mapped[str] = mapped_column(Text, nullable=True)
    support_targets: Mapped[str] = mapped_column(Text, nullable=True)
    support_type: Mapped[str] = mapped_column(Text, nullable=True)

    detail_url: Mapped[str] = mapped_column(Text, nullable=True)
    law: Mapped[str] = mapped_column(Text, nullable=True)

    # Age
    JA0110: Mapped[int] = mapped_column(Integer, nullable=True, index=True, comment="Start Age")
    JA0111: Mapped[int] = mapped_column(Integer, nullable=True, index=True, comment="End Age")

    # Gender
    JA0101: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Is for Male")
    JA0102: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Is for Female")

    # Income
    JA0201: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Income is lte 50%")
    JA0202: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Income is gte 51% and lte 75%")
    JA0203: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Income is gte 76% and lte 100%")
    JA0204: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Income is gte 101% and lte 200%")
    JA0205: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Income is gte 201%")

    # Life
    JA0301: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Prospective parents / Infertility")
    JA0302: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Pregnant women")
    JA0303: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Childbirth / Adoption")

    # Primary Industry
    JA0313: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Farmers")
    JA0314: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Fishermen")
    JA0315: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Livestock farmers")
    JA0316: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Forestry workers")

    # Academic Status
    JA0317: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Elementary school students")
    JA0318: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Middle school students")
    JA0319: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="High school students")
    JA0320: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="University students / Graduate students")
    JA0322: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Not applicable")

    # Working Status
    JA0326: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Workers / Office employees")
    JA0327: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Job seekers / Unemployed")

    # Other
    JA0328: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="People with disabilities")
    JA0329: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Veterans")
    JA0330: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Patients / People with diseases")

    # Family
    JA0401: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Multicultural families")
    JA0402: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="North Korean defectors")
    JA0403: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Single-parent / Grandparent families")
    JA0404: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Single-person households")
    JA0410: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Not applicable")
    JA0411: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Multi Child Family")
    JA0412: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Homeless households")
    JA0413: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="New residents")
    JA0414: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Extended families")

    # Business
    JA1101: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Prospective entrepreneurs")
    JA1102: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Currently operating businesses")
    JA1103: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Financially struggling / Closing businesses")
    JA1201: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Food service industry")
    JA1202: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Manufacturing industry")
    JA1299: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Other industries")

    # Organization
    JA2101: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Small and medium enterprises (SMEs)")
    JA2102: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Social welfare facilities")
    JA2103: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Institutions / Organizations")
    JA2201: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Manufacturing industry")
    JA2202: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Agriculture, forestry, and fishery")
    JA2203: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Information and communication industry")
    JA2299: Mapped[bool] = mapped_column(Boolean, nullable=True, comment="Other industries")
