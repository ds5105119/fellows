from src.app.fellows.model.help import Help
from src.core.models.repository import (
    ABaseCreateRepository,
    ABaseDeleteRepository,
    ABaseReadRepository,
    ABaseUpdateRepository,
)


class HelpCreateRepository(ABaseCreateRepository[Help]):
    pass


class HelpReadRepository(ABaseReadRepository[Help]):
    pass


class HelpUpdateRepository(ABaseUpdateRepository[Help]):
    pass


class HelpDeleteRepository(ABaseDeleteRepository[Help]):
    pass


class HelpRepository(
    HelpCreateRepository,
    HelpReadRepository,
    HelpUpdateRepository,
    HelpDeleteRepository,
):
    pass
