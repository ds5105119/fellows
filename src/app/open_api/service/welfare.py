from datetime import datetime
from typing import Annotated, Sequence

from fastapi import HTTPException, Query
from sqlalchemy import and_, desc, or_

from src.app.open_api.repository.welfare import GovWelfareRepository
from src.app.open_api.schema.welfare import WelfareDto
from src.app.user.model.user_data import AcademicStatus, UserData
from src.app.user.repository.user_data import UserDataRepository
from src.core.dependencies.auth import User, get_current_user_without_error
from src.core.dependencies.db import postgres_session


class GovWelfareService:
    def __init__(self, repository: GovWelfareRepository, user_data_repository: UserDataRepository):
        self.repository = repository
        self.user_data_repository = user_data_repository

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
                filters = and_(filters, self.repository.model.support_type.contains(data.tag))
            else:
                filters = [self.repository.model.support_type.contains(data.tag)]

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
                self.repository.model.document,
                self.repository.model.receiving_agency,
                self.repository.model.offc_name,
                self.repository.model.contact,
                self.repository.model.support_details,
            ],
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
