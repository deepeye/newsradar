"""Organization configuration model"""
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OrgConfig(BaseModel):
    __tablename__ = "org_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    domains: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment="Focus areas e.g. ['财经', '民生']"
    )
    style: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment="Reporting style e.g. ['客观', '严谨']"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
