from src.app.fellows.model.help import Help
from src.app.fellows.repository.frappe import FrappeRepository
from src.app.fellows.repository.help import HelpRepository
from src.app.fellows.service.help import HelpService
from src.app.fellows.service.project import ProjectService
from src.app.user.api.dependencies import alert_repository, cloud_service
from src.core.dependencies.auth import keycloak_admin
from src.core.dependencies.db import Redis
from src.core.dependencies.infra import frappe_client, openai_client

frappe_repository = FrappeRepository(frappe_client)
project_service = ProjectService(
    openai_client, frappe_client, cloud_service, frappe_repository, alert_repository, keycloak_admin, Redis
)

help_repository = HelpRepository(Help)
help_service = HelpService(help_repository)
