from fastapi import HTTPException

from src.app.fellows.repository.frappe import FrappReadRepository
from src.app.fellows.schema.contract import (
    ERPNextContract,
    ERPNextContractPaginatedResponse,
    ERPNextContractRequest,
    UpdateERPNextContract,
    UpdateERPNextContractForInner,
)
from src.core.utils.frappeclient import AsyncFrappeClient


class ContractCreateRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client


class ContractReadRepository(FrappReadRepository):
    async def get_contract(self, name: str):
        data = await self.frappe_client.get_doc("Contract", name)
        if not data:
            raise HTTPException(status_code=404, detail="contract not found")
        return ERPNextContract(**data)

    async def get_contracts(
        self,
        data: ERPNextContractRequest,
        sub: str,
    ):
        accessible_projects = await self.get_project_names(sub)

        if not accessible_projects:
            return ERPNextContractPaginatedResponse(items=[])

        accessible_projects_names = [p["project_name"] for p in accessible_projects]

        filters = {
            "document_type": ["=", "Project"],
            "document_name": ["in", accessible_projects_names],  # 고침
        }
        or_filters = {}

        if data.keyword:
            filters["custom_name"] = ["like", f"%{data.keyword}%"]
        if data.start:
            filters["start_date"] = [">=", data.start]
        if data.end:
            filters["start_date"] = ["<=", data.end]
        if type(data.docstatus) is int:
            filters["docstatus"] = ["=", data.docstatus]
        if type(data.is_signed) is bool:
            filters["is_signed"] = ["=", data.is_signed]
        if isinstance(data.project_id, str):
            if data.project_id not in accessible_projects_names:
                raise HTTPException(status_code=403, detail="Project not found")
            filters["document_name"] = ["=", data.project_id]
        elif isinstance(data.project_id, list):
            if not set(data.project_id).issubset(accessible_projects_names):
                raise HTTPException(status_code=403, detail="Project not found")
            filters["document_name"] = ["in", data.project_id]

        order_by = ["modified asc"]
        if isinstance(data.order_by, str):
            order_by = data.order_by
        elif isinstance(data.order_by, list):
            order_by = [f"{o.split('.')[0]} desc" if o.split(".")[-1] == "desc" else o for o in data.order_by]

        contracts = await self.frappe_client.get_list(
            "Contract",
            filters=filters,
            or_filters=or_filters,
            limit_start=data.page * data.size,
            limit_page_length=data.size,
            order_by=order_by,
        )

        return ERPNextContractPaginatedResponse.model_validate({"items": contracts}, from_attributes=True)


class ContractUpdateRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client

    async def update_contract_by_id(self, name: str, data: UpdateERPNextContractForInner | UpdateERPNextContract):
        updated_contract = await self.frappe_client.update(
            {
                "doctype": "Contract",
                "name": name,
                **data.model_dump(by_alias=True, exclude_unset=True),
            }
        )

        return ERPNextContract(**updated_contract)


class ContractDeleteRepository:
    def __init__(
        self,
        frappe_client: AsyncFrappeClient,
    ):
        self.frappe_client = frappe_client


class ContractRepository(
    ContractCreateRepository,
    ContractReadRepository,
    ContractUpdateRepository,
    ContractDeleteRepository,
):
    pass
