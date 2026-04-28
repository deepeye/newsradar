"""Authentication service"""
from typing import Optional
from uuid import UUID

from app.core.security import verify_password, hash_password, create_access_token
from app.core.config import settings
from app.repositories.user_repo import UserRepository
from app.models.user import User, UserRole
from app.core.exceptions import UnauthorizedException


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate(
        self, username: str, password: str
    ) -> Optional[dict]:
        user = await self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid username or password")
        if not user.is_active:
            raise UnauthorizedException("User account is disabled")

        token = create_access_token(data={"sub": str(user.id)})
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_HOURS * 3600,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role.value if isinstance(user.role, UserRole) else user.role,
            },
        }

    async def create_user(
        self,
        username: str,
        password: str,
        display_name: str = "",
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        existing = await self.user_repo.get_by_username(username)
        if existing:
            raise ValueError(f"Username '{username}' already exists")
        hashed = hash_password(password)
        return await self.user_repo.create(
            username=username,
            password_hash=hashed,
            display_name=display_name,
            role=role,
        )