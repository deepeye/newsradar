"""种子数据脚本 - 创建基础数据源组"""
import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import db_manager
from app.storage.models import SourceGroup


# 基础数据源组（不含数据源，数据源通过 API 动态添加）
BASE_GROUPS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "热榜组",
        "collect_interval": 5,
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "name": "微博KOL组",
        "collect_interval": 30,
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "name": "X KOL组",
        "collect_interval": 30,
    },
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "name": "Reddit组",
        "collect_interval": 30,
    },
]


async def seed_groups(db: AsyncSession) -> None:
    """创建基础数据源组"""
    for group_data in BASE_GROUPS:
        group = SourceGroup(
            id=uuid.UUID(group_data["id"]),
            name=group_data["name"],
            collect_interval=group_data["collect_interval"],
            is_active=True,
        )
        db.add(group)

    await db.commit()
    print(f"Seeded {len(BASE_GROUPS)} source groups")


async def main() -> None:
    """主函数"""
    await db_manager.initialize()
    async with db_manager.session() as session:
        await seed_groups(session)
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())