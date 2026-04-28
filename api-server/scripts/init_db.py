"""Initialize database with default admin user"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db_manager
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository
from app.models.user import UserRole


async def init():
    await db_manager.initialize()
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        auth_service = AuthService(user_repo)

        try:
            admin = await auth_service.create_user(
                username="admin",
                password="admin123",
                display_name="管理员",
                role=UserRole.ADMIN,
            )
            print(f"Created admin user: {admin.username}")
        except ValueError as e:
            print(f"Admin user already exists: {e}")

        try:
            editor = await auth_service.create_user(
                username="editor",
                password="editor123",
                display_name="编辑",
                role=UserRole.EDITOR,
            )
            print(f"Created editor user: {editor.username}")
        except ValueError as e:
            print(f"Editor user already exists: {e}")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(init())