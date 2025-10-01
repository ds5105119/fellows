from pydantic import BaseModel, Field


class ContactRequest(BaseModel):
    name: str
    company: str | None = Field(None)
    level: str | None = Field(None)
    budget: str
    email: str
    phone: str | None = Field(None)
    description: str
