from src.app.fellows.repository.frappe import FrappeRepository
from src.app.fellows.service.project import ProjectService
from src.app.user.api.dependencies import alert_repository
from src.core.dependencies.auth import keycloak_admin
from src.core.dependencies.infra import frappe_client, openai_client

frappe_repository = FrappeRepository(frappe_client)
project_service = ProjectService(openai_client, frappe_client, frappe_repository, alert_repository, keycloak_admin)
