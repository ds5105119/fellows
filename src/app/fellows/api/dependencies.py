from src.app.fellows.service.project import ProjectService
from src.core.dependencies.infra import frappe_client, openai_client

project_service = ProjectService(openai_client, frappe_client)
