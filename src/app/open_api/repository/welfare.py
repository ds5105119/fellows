from src.app.open_api.model.welfare import GovWelfare
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class GovWelfareCreateRepository(ABaseCreateRepository[GovWelfare]):
    pass


class GovWelfareReadRepository(ABaseReadRepository[GovWelfare]):
    pass


class GovWelfareUpdateRepository(ABaseUpdateRepository[GovWelfare]):
    pass


class GovWelfareDeleteRepository(ABaseDeleteRepository[GovWelfare]):
    pass


class GovWelfareRepository(
    GovWelfareCreateRepository,
    GovWelfareReadRepository,
    GovWelfareUpdateRepository,
    GovWelfareDeleteRepository,
):
    pass
