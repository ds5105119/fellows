from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base


class Help(Base):
    __tablename__ = "fellows_help"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    title_image: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(Text, nullable=True)
