import enum

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base


class AcademicStatus(enum.Enum):
    none = 0
    elementary_stu = 1
    middle_stu = 2
    high_stu = 3
    university_stu = 4


class UserData(Base):
    __tablename__ = "user_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sub: Mapped[int] = mapped_column(String, unique=True, nullable=False)

    overcome: Mapped[int] = mapped_column(Integer, nullable=True)
    household_size: Mapped[int] = mapped_column(Integer, nullable=True)

    multicultural: Mapped[bool] = mapped_column(Boolean, default=False)
    north_korean: Mapped[bool] = mapped_column(Boolean, default=False)
    single_parent_or_grandparent: Mapped[bool] = mapped_column(Boolean, default=False)
    homeless: Mapped[bool] = mapped_column(Boolean, default=False)
    new_resident: Mapped[bool] = mapped_column(Boolean, default=False)
    multi_child_family: Mapped[bool] = mapped_column(Boolean, default=False)
    extend_family: Mapped[bool] = mapped_column(Boolean, default=False)

    disable: Mapped[bool] = mapped_column(Boolean, default=False)
    veteran: Mapped[bool] = mapped_column(Boolean, default=False)
    disease: Mapped[bool] = mapped_column(Boolean, default=False)

    prospective_parents_or_infertility: Mapped[bool] = mapped_column(Boolean, default=False)
    pregnant: Mapped[bool] = mapped_column(Boolean, default=False)
    childbirth_or_adoption: Mapped[bool] = mapped_column(Boolean, default=False)

    farmers: Mapped[bool] = mapped_column(Boolean, default=False)
    fishermen: Mapped[bool] = mapped_column(Boolean, default=False)
    livestock_farmers: Mapped[bool] = mapped_column(Boolean, default=False)
    forestry_workers: Mapped[bool] = mapped_column(Boolean, default=False)

    unemployed: Mapped[bool] = mapped_column(Boolean, default=False)
    employed: Mapped[bool] = mapped_column(Boolean, default=False)

    academic_status: Mapped[int] = mapped_column(Integer, default=0)
    working_status: Mapped[int] = mapped_column(Integer, default=0)


class UserBusinessData(Base):
    __tablename__ = "user_business_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    ja1101: Mapped[bool] = mapped_column(Boolean, default=False)  # 예비창업자
    ja1102: Mapped[bool] = mapped_column(Boolean, default=False)  # 영업중
    ja1103: Mapped[bool] = mapped_column(Boolean, default=False)  # 생계곤란/폐업예정자

    ja1201: Mapped[bool] = mapped_column(Boolean, default=False)  # 음식적업
    ja1202: Mapped[bool] = mapped_column(Boolean, default=False)  # 제조업
    ja1299: Mapped[bool] = mapped_column(Boolean, default=False)  # 기타업종

    ja2101: Mapped[bool] = mapped_column(Boolean, default=False)  # 중소기업
    ja2102: Mapped[bool] = mapped_column(Boolean, default=False)  # 사회복지시설
    ja2103: Mapped[bool] = mapped_column(Boolean, default=False)  # 기관/단체

    ja2201: Mapped[bool] = mapped_column(Boolean, default=False)  # 제조업
    ja2202: Mapped[bool] = mapped_column(Boolean, default=False)  # 농업,임업 및 어업
    ja2203: Mapped[bool] = mapped_column(Boolean, default=False)  # 정보통신업
    ja2299: Mapped[bool] = mapped_column(Boolean, default=False)  # 기타업종
