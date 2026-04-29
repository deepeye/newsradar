"""Auth request/response schemas"""
from pydantic import Field

from app.schemas.common import CamelModel


class LoginRequest(CamelModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class UserInfo(CamelModel):
    id: str
    username: str
    display_name: str
    role: str


class LoginResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo