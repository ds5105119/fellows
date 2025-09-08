from pydantic import BaseModel


class HelpCreate(BaseModel):
    title: str
    title_image: str
    content: str
    summary: str | None = None
    category: str | None = None


class HelpRead(BaseModel):
    id: str
    title: str
    title_image: str
    content: str
    summary: str | None = None
    category: str | None = None


class HelpsRead(BaseModel):
    items: list[HelpRead]


class HelpUpdate(BaseModel):
    title: str
    title_image: str
    content: str
    summary: str | None = None
    category: str | None = None
