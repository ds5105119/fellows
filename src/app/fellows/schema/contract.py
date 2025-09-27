import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CustomContractStatus(str, Enum):
    UNSIGNED = "Unsigned"
    SIGNED = "Signed"
    PAYMENT = "Payment"
    ACTIVE = "Active"
    COMPLETE = "Complete"
    INACTIVE = "Inactive"


class ERPNextContract(BaseModel):
    name: str
    owner: str
    custom_name: str
    creation: datetime.datetime
    modified: datetime.datetime
    modified_by: str
    docstatus: int
    idx: int
    party_type: str | None = Field(default=None)
    is_signed: bool | None = Field(default=None)
    custom_subscribe: bool | None = Field(default=None)
    party_name: str | None = Field(default=None)
    party_user: str | None = Field(default=None)
    status: str | None = Field(default=None)
    fulfilment_status: str | None = Field(default=None)
    party_full_name: str | None = Field(default=None)
    start_date: datetime.date | None = Field(default=None)
    end_date: datetime.date | None = Field(default=None)
    custom_contract_status: CustomContractStatus
    custom_fee: int | None = Field(default=None)
    custom_down_payment: float | None = Field(default=None)
    custom_balance: float | None = Field(default=None)
    custom_maintenance: int | None = Field(default=None)
    signee: str | None = Field(default=None)
    signed_on: datetime.datetime | None = Field(default=None)
    ip_address: str | None = Field(default=None)
    contract_template: str | None = Field(default=None)
    contract_terms: str | None = Field(default=None)
    requires_fulfilment: int | None = Field(default=None)
    fulfilment_deadline: datetime.datetime | None = Field(default=None)
    signee_company: str | None = Field(default=None)
    signed_by_company: str | None = Field(default=None)
    document_type: str | None = Field(default=None)
    document_name: str | None = Field(default=None)
    amended_from: str | None = Field(default=None)


class UserERPNextContract(BaseModel):
    name: str
    owner: str
    custom_name: str
    creation: datetime.datetime
    modified: datetime.datetime
    modified_by: str
    docstatus: int
    idx: int
    is_signed: bool | None = Field(default=None)
    custom_subscribe: bool | None = Field(default=None)
    party_name: str | None = Field(default=None)
    status: str | None = Field(default=None)
    start_date: datetime.date | None = Field(default=None)
    end_date: datetime.date | None = Field(default=None)
    custom_fee: int | None = Field(default=None)
    custom_contract_status: CustomContractStatus
    custom_down_payment: float | None = Field(default=None)
    custom_balance: float | None = Field(default=None)
    custom_maintenance: int | None = Field(default=None)
    signee: str | None = Field(default=None)
    signed_on: datetime.datetime | None = Field(default=None)
    signee_company: str | None = Field(default=None)
    ip_address: str | None = Field(default=None)
    contract_template: str | None = Field(default=None)
    contract_terms: str | None = Field(default=None)
    document_type: str | None = Field(default=None)
    document_name: str | None = Field(default=None)


class UpdateERPNextContract(BaseModel):
    signee: str | None = Field(default=None)
    signed_on: datetime.datetime | None = Field(default=None)
    signee_company: str | None = Field(default=None)
    ip_address: str | None = Field(default=None)
    is_signed: bool | None = Field(default=None)
    custom_contract_status: CustomContractStatus | None = Field(default=None)


class ERPNextContractRequest(BaseModel):
    page: int = Field(0, ge=0, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Page size")
    project_id: list[str] | str | None = Field(default=None)
    keyword: str | None = Field(default=None)
    order_by: list[str] | str = Field(default="modified")
    docstatus: int | None = Field(default=None)
    is_signed: bool | None = Field(default=None)
    start: datetime.date | None = Field(default=None)
    end: datetime.date | None = Field(default=None)


class ERPNextContractPaginatedResponse(BaseModel):
    items: list[UserERPNextContract]
