from src.app.fellows.repository.frappe import FrappeRepository
from src.app.fellows.service.project import ProjectService
from src.core.dependencies.infra import frappe_client, openai_client

frappe_repository = FrappeRepository(frappe_client)
project_service = ProjectService(openai_client, frappe_client, frappe_repository)
