from sqlalchemy import Boolean, DateTime, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base


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
