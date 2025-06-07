from src.app.open_api.model.fiscal import Fiscal, FiscalByYear, FiscalByYearOffc
from src.app.open_api.model.welfare import GovWelfare
from src.app.open_api.repository.fiscal import FiscalByYearOffcRepository, FiscalByYearRepository, FiscalRepository
from src.app.open_api.repository.welfare import GovWelfareRepository
from src.app.open_api.service.fiscal import FiscalService
from src.app.open_api.service.welfare import GovWelfareService
from src.app.user.api.dependencies import user_business_data_repository, user_data_repository

fiscal_repository = FiscalRepository(Fiscal)
fiscal_by_year_repository = FiscalByYearRepository(FiscalByYear)
fiscal_by_year_offc_repository = FiscalByYearOffcRepository(FiscalByYearOffc)
fiscal_service = FiscalService(fiscal_repository, fiscal_by_year_repository, fiscal_by_year_offc_repository)

gov_welfare_repository = GovWelfareRepository(GovWelfare)
gov_welfare_service = GovWelfareService(gov_welfare_repository, user_data_repository, user_business_data_repository)
