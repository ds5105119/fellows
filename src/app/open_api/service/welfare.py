from datetime import datetime
from typing import Annotated, Sequence

from fastapi import HTTPException, Query
from sqlalchemy import and_, cast, desc, func, or_
from sqlalchemy.dialects.postgresql import TSVECTOR

from src.app.open_api.repository.welfare import GovWelfareRepository
from src.app.open_api.schema.welfare import WelfareDto
from src.app.user.model.user_data import AcademicStatus, UserBusinessData, UserData
from src.app.user.repository.user_data import UserBusinessDataRepository, UserDataRepository
from src.core.dependencies.auth import User, get_current_user_without_error
from src.core.dependencies.db import postgres_session


class GovWelfareService:
    def __init__(
        self,
        repository: GovWelfareRepository,
        user_data_repository: UserDataRepository,
        user_business_data_repository: UserBusinessDataRepository,
    ):
        self.repository = repository
        self.user_data_repository = user_data_repository
        self.user_business_data_repository = user_business_data_repository

    @staticmethod
    def _user_data_filter(
        user_data: UserData,
        status_mapping: dict,
        primary_status_field,
        filter_on_exist: Sequence | None = None,
        filter_on_empty: Sequence | None = None,
    ):
        if user_data:
            primary_column = status_mapping.get(primary_status_field)

            if primary_column:
                return or_(
                    primary_column == True,
                    and_(*(col == False for col in status_mapping.values())),
                    *(filter_on_exist or []),
                )
            return or_(
                and_(*(col == True for col in status_mapping.values())),
                and_(*(col == False for col in status_mapping.values())),
                *(filter_on_empty or []),
            )

    def _type_filter(self, type):
        if type == "user":
            return or_(
                self.repository.model.user_type.contains("개인"),
                self.repository.model.user_type.contains("가구"),
            )
        else:
            return or_(
                self.repository.model.user_type.contains("법인"),
                self.repository.model.user_type.contains("시설"),
                self.repository.model.user_type.contains("단체"),
                self.repository.model.user_type.contains("소상공인"),
            )

    def _age_filter(self, user: User):
        if user.birthdate is None:
            return None
        now = datetime.now()
        age = now.year - user.birthdate.year
        age = age - 1 if (now.month, now.day) < (user.birthdate.month, user.birthdate.day) else age
        return and_(
            or_(
                self.repository.model.JA0110 <= age,
                self.repository.model.JA0110 is None,
            ),
            or_(
                self.repository.model.JA0111 >= age,
                self.repository.model.JA0111 is None,
            ),
        )

    def _gender_filter(self, user: User):
        if user.gender is None:
            return None
        if user.gender == "male":
            return self.repository.model.JA0101 == True
        elif user.gender == "female":
            return self.repository.model.JA0102 == True
        else:
            return None

    def _overcome_filter(self, user_data: UserData):
        if not user_data or user_data.overcome is None or user_data.household_size is None:
            return None

        overcome_ratio = {
            1: 2392013,
            2: 3932658,
            3: 5025253,
            4: 6097773,
            5: 7108192,
            6: 8064805,
            7: 8988428,
        }.get(user_data.household_size, 8988428 + 923623 * (user_data.household_size - 7))

        default_filter = and_(
            self.repository.model.JA0201 == False,
            self.repository.model.JA0202 == False,
            self.repository.model.JA0203 == False,
            self.repository.model.JA0204 == False,
            self.repository.model.JA0205 == False,
        )

        filters = [
            (0.5, self.repository.model.JA0201 == True),
            (0.75, self.repository.model.JA0202 == True),
            (1.0, self.repository.model.JA0203 == True),
            (2.0, self.repository.model.JA0204 == True),
            (float("inf"), self.repository.model.JA0205 == True),
        ]

        for threshold, condition in filters:
            if overcome_ratio <= threshold:
                return or_(default_filter, condition)

    def _family_status_filter(self, user_data: UserData):
        if user_data is None:
            return None
        return or_(
            self.repository.model.JA0401 == user_data.multicultural,
            self.repository.model.JA0402 == user_data.north_korean,
            self.repository.model.JA0403 == user_data.single_parent_or_grandparent,
            self.repository.model.JA0404 == True if user_data.household_size == 1 else None,
            self.repository.model.JA0410 == True,
            self.repository.model.JA0411 == user_data.multi_child_family,
            self.repository.model.JA0412 == user_data.homeless,
            self.repository.model.JA0413 == user_data.new_resident,
            self.repository.model.JA0414 == user_data.extend_family,
            and_(
                self.repository.model.JA0401 == False,
                self.repository.model.JA0402 == False,
                self.repository.model.JA0403 == False,
                self.repository.model.JA0404 == False,
                self.repository.model.JA0410 == False,
                self.repository.model.JA0411 == False,
                self.repository.model.JA0412 == False,
                self.repository.model.JA0413 == False,
                self.repository.model.JA0414 == False,
            ),
        )

    def _other_status_filter(self, user_data: UserData):
        if user_data is None:
            return None
        return or_(
            self.repository.model.JA0328 == user_data.disable,
            self.repository.model.JA0329 == user_data.veteran,
            self.repository.model.JA0330 == user_data.disease,
        )

    def _life_status_filter(self, user_data: UserData):
        if user_data is None:
            return None
        return or_(
            self.repository.model.JA0301 == user_data.prospective_parents_or_infertility,
            self.repository.model.JA0302 == user_data.pregnant,
            self.repository.model.JA0303 == user_data.childbirth_or_adoption,
        )

    def _primary_industry_status_filter(self, user_data: UserData):
        if user_data is None:
            return None
        return or_(
            self.repository.model.JA0313 == user_data.farmers,
            self.repository.model.JA0314 == user_data.fishermen,
            self.repository.model.JA0315 == user_data.livestock_farmers,
            self.repository.model.JA0316 == user_data.forestry_workers,
        )

    def _academic_status_filter(self, user_data: UserData):
        if user_data:
            status_mapping = {
                AcademicStatus.elementary_stu: self.repository.model.JA0317,
                AcademicStatus.middle_stu: self.repository.model.JA0318,
                AcademicStatus.high_stu: self.repository.model.JA0319,
                AcademicStatus.university_stu: self.repository.model.JA0320,
            }
            return self._user_data_filter(
                user_data,
                status_mapping,
                user_data.academic_status,
                [self.repository.model.JA0322 == True],
                [self.repository.model.JA0322 == True],
            )

    async def get_personal_welfare(
        self,
        session: postgres_session,
        data: Annotated[WelfareDto, Query()],
        user: get_current_user_without_error,
    ):
        filters = None
        if not hasattr(self.repository.model, data.order_by):
            raise HTTPException(status_code=404, detail="Order Column name was Not found")

        if user:
            user_data = await self.user_data_repository.get_user_data(session, sub=user.sub)

            if user_data:
                or_conditions = [
                    c
                    for c in (
                        self._family_status_filter(user_data),
                        self._life_status_filter(user_data),
                        self._other_status_filter(user_data),
                        self._primary_industry_status_filter(user_data),
                    )
                    if c is not None
                ]
                and_conditions = [
                    c
                    for c in (
                        self._academic_status_filter(user_data),
                        self._overcome_filter(user_data),
                        self._gender_filter(user),
                        self._age_filter(user),
                    )
                    if c is not None
                ]

                filters = and_(or_(*or_conditions), *and_conditions) if or_conditions else and_(*and_conditions)

        if data.tag:
            if filters:
                filters = and_(
                    filters,
                    self.repository.model.support_type.contains(data.tag),
                    self._type_filter("user"),
                )
            else:
                filters = [
                    self.repository.model.support_type.contains(data.tag),
                    self._type_filter("user"),
                ]

        result = await self.repository.get_page(
            session,
            data.page,
            data.size,
            filters,
            [
                self.repository.model.id,
                self.repository.model.views,
                self.repository.model.service_id,
                self.repository.model.service_name,
                self.repository.model.service_summary,
                self.repository.model.service_category,
                self.repository.model.service_conditions,
                self.repository.model.service_description,
                self.repository.model.apply_period,
                self.repository.model.apply_url,
                self.repository.model.detail_url,
                self.repository.model.document,
                self.repository.model.receiving_agency,
                self.repository.model.offc_name,
                self.repository.model.contact,
                self.repository.model.support_details,
            ],
            [desc(getattr(self.repository.model, data.order_by))],
        )

        return result.mappings().all()

    async def get_business_welfare(
        self,
        session: postgres_session,
        data: Annotated[WelfareDto, Query()],
        user: get_current_user_without_error,
    ):
        # order_by 가 컬럼에 존재하지 않는 경우 404
        if not hasattr(self.repository.model, data.order_by):
            raise HTTPException(status_code=404, detail="Order Column name was Not found")

        # 변수 초기화
        filters = []
        specific_filter = None
        business_data: UserBusinessData | None = None
        columns = [
            self.repository.model.id,
            self.repository.model.views,
            self.repository.model.service_id,
            self.repository.model.service_name,
            self.repository.model.service_summary,
            self.repository.model.service_category,
            self.repository.model.service_conditions,
            self.repository.model.service_description,
            self.repository.model.apply_period,
            self.repository.model.apply_url,
            self.repository.model.detail_url,
            self.repository.model.document,
            self.repository.model.receiving_agency,
            self.repository.model.offc_name,
            self.repository.model.dept_name,
            self.repository.model.dept_type,
            self.repository.model.contact,
            self.repository.model.support_details,
            self.repository.model.support_targets,
        ]

        # 기본 필터 초기화
        if data.tag:
            filters.append(self.repository.model.support_type.contains(data.tag))
        if data.keyword:
            filters.append(
                cast(func.to_tsvector("simple", self.repository.model.service_name), TSVECTOR)
                .op("||")(cast(func.to_tsvector("simple", self.repository.model.service_summary), TSVECTOR))
                .op("@@")(func.websearch_to_tsquery("simple", data.keyword))
            )
        filters.append(self._type_filter("business"))
        filters = [f for f in filters if f is not None]

        # business_data 불러오기
        if user:
            business_data = await self.user_business_data_repository.get_business_data(session, sub=user.sub)

        if business_data:
            user_true_ja_attributes = {
                name
                for name in business_data.__table__.columns.keys()
                if name.startswith("JA") and getattr(business_data, name, False)
            }

            if user_true_ja_attributes:
                condition_groups = {
                    "status": {"JA1101", "JA1102", "JA1103"},
                    "industry": {"JA1201", "JA1202", "JA1299", "JA2201", "JA2202", "JA2203", "JA2299"},
                    "org_type": {"JA2101", "JA2102", "JA2103"},
                }

                required_group_checks = []

                for group_name, group_codes in condition_groups.items():
                    # 하나라도 True를 요구하는 그룹이 있습니까?
                    service_requires_group = or_(*[getattr(self.repository.model, ja) == True for ja in group_codes])

                    # 그렇다면 하나라도 일치하는 정보가 있습니까?
                    user_matches_group_requirement = or_(
                        *[
                            and_(getattr(self.repository.model, ja) == True, ja in user_true_ja_attributes)
                            for ja in group_codes
                        ]
                    )

                    group_check_clause = or_(~service_requires_group, user_matches_group_requirement)
                    required_group_checks.append(group_check_clause)

                if required_group_checks:
                    specific_filter = and_(*required_group_checks)
                else:
                    pass

        if specific_filter is not None:
            filters = [*filters, specific_filter]

        result = await self.repository.get_page(
            session,
            data.page,
            data.size,
            filters,
            columns,
            [desc(getattr(self.repository.model, data.order_by))],
        )

        return result.mappings().all()

    async def get_welfare(
        self,
        session: postgres_session,
        id: Annotated[str, Query()],
    ):
        result = await self.repository.get(session, [self.repository.model.service_id == id])
        return result.mappings().first()

    async def get_welfare_id(self, session: postgres_session):
        result = await self.repository.get(session, filters=[], columns=[self.repository.model.service_id])
        return result.mappings().all()
