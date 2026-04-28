"""Seed demo data for development"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db_manager
from app.repositories.org_config_repo import OrgConfigRepository


async def seed():
    await db_manager.initialize()
    async with db_manager.session() as session:
        # Create default org config
        org_repo = OrgConfigRepository(session)
        config = await org_repo.create_or_update(
            name="默认媒体机构",
            domains=["财经", "民生", "科技"],
            style=["客观", "严谨", "深度"],
        )
        print(f"Created org config: {config.name}")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(seed())