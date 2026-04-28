"""User model"""
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class UserRole(str, PyEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default=""
    )
    role: Mapped[UserRole] = mapped_column(
        String(20), nullable=False, default=UserRole.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
