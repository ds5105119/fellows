from src.app.gov_api.model.fiscal import Fiscal, FiscalByYear, FiscalByYearOffc
from src.core.models.repository import ABaseReadRepository


class FiscalReadRepository(ABaseReadRepository[Fiscal]):
    pass


class FiscalByYearReadRepository(ABaseReadRepository[FiscalByYear]):
    pass


class FiscalByYearOffcReadRepository(ABaseReadRepository[FiscalByYearOffc]):
    pass


class FiscalRepository(FiscalReadRepository):
    pass


class FiscalByYearRepository(FiscalByYearReadRepository):
    pass


class FiscalByYearOffcRepository(FiscalByYearOffcReadRepository):
    pass
