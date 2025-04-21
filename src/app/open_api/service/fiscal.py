from typing import Annotated

from fastapi import Query
from sqlalchemy import desc

from src.app.open_api.repository.fiscal import FiscalByYearOffcRepository, FiscalByYearRepository, FiscalRepository
from src.app.open_api.schema.fiscal import FiscalByYearDto, FiscalByYearOffcDto, FiscalDto
from src.core.dependencies.db import postgres_session


class FiscalService:
    def __init__(
        self,
        fiscal_repository: FiscalRepository,
        fiscal_by_year_repository: FiscalByYearRepository,
        fiscal_by_year_offc_repository: FiscalByYearOffcRepository,
    ):
        self.fiscal_repository = fiscal_repository
        self.fiscal_by_year_repository = fiscal_by_year_repository
        self.fiscal_by_year_offc_repository = fiscal_by_year_offc_repository

    async def get_fiscal(
        self,
        session: postgres_session,
        data: Annotated[FiscalDto, Query()],
    ):
        filters = []
        if data.start_year:
            filters.append(self.fiscal_repository.model.FSCL_YY >= int(data.start_year))
        if data.end_year:
            filters.append(self.fiscal_repository.model.FSCL_YY <= int(data.end_year))
        if data.dept_code:
            filters.append(self.fiscal_repository.model.NORMALIZED_DEPT_NO == data.dept_code)
        elif data.offc_name:
            filters.append(self.fiscal_repository.model.OFFC_NM == data.offc_name)

        result = await self.fiscal_repository.get_page(
            session,
            data.page,
            data.size,
            filters=filters,
            orderby=[desc(getattr(self.fiscal_repository.model, data.order_by))],
        )

        return result.mappings().all()

    async def get_fiscal_by_year(
        self,
        session: postgres_session,
        data: Annotated[FiscalByYearDto, Query()],
    ):
        filters = []
        if data.start_year:
            filters.append(self.fiscal_by_year_repository.model.FSCL_YY >= int(data.start_year))
        if data.end_year:
            filters.append(self.fiscal_by_year_repository.model.FSCL_YY <= int(data.end_year))

        result = await self.fiscal_by_year_repository.get_page(
            session,
            data.page,
            data.size,
            filters=filters,
            orderby=[desc(getattr(self.fiscal_by_year_repository.model, data.order_by))],
        )

        return result.mappings().all()

    async def get_fiscal_by_year_offc(
        self,
        session: postgres_session,
        data: Annotated[FiscalByYearOffcDto, Query()],
    ):
        filters = []
        if data.start_year:
            filters.append(self.fiscal_by_year_offc_repository.model.FSCL_YY >= int(data.start_year))
        if data.end_year:
            filters.append(self.fiscal_by_year_offc_repository.model.FSCL_YY <= int(data.end_year))
        if data.dept_code:
            filters.append(self.fiscal_by_year_offc_repository.model.NORMALIZED_DEPT_NO == data.dept_code)
        elif data.offc_name:
            filters.append(self.fiscal_by_year_offc_repository.model.OFFC_NM == data.offc_name)

        result = await self.fiscal_by_year_offc_repository.get_page(
            session,
            data.page,
            data.size,
            filters=filters,
            orderby=[desc(getattr(self.fiscal_by_year_offc_repository.model, data.order_by))],
        )

        return result.mappings().all()
