"""种子数据脚本 - 初始化数据源"""
import asyncio
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import db_manager
from app.storage.models import (
    SourceGroup, DataSource, DataSourceType, CollectorType, SourceStatus
)


# 微博 KOL 媒体账号
WEIBO_KOL_ACCOUNTS = [
    {
        "name": "北京头条",
        "uid": "1644948230",
        "priority": 8,
    },
    {
        "name": "环球时报",
        "uid": "1974576991",
        "priority": 8,
    },
    {
        "name": "澎湃新闻",
        "uid": "5044281310",
        "priority": 8,
    },
    {
        "name": "新京报",
        "uid": "1644114654",
        "priority": 8,
    },
    {
        "name": "南方都市报",
        "uid": "1644489953",
        "priority": 8,
    },
]

# 热榜数据源
HOTLIST_SOURCES = [
    {
        "name": "微博热搜",
        "type": DataSourceType.HOTLIST,
        "priority": 9,
        "config": {
            "url": "https://weibo.com/ajax/side/hotSearch",
            "method": "GET",
            "parse_type": "json",
            "parse_rules": {
                "container": "data.realtime",
                "title": "note",
                "rank": "rank",
                "heat": "num",
                "link": "scheme",
            },
        },
    },
    {
        "name": "知乎热榜",
        "type": DataSourceType.HOTLIST,
        "priority": 8,
        "config": {
            "url": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
            "method": "GET",
            "parse_type": "json",
            "parse_rules": {
                "container": "data",
                "title": "target.title",
                "heat": "detail_text",
                "link": "target.url",
            },
        },
    },
    {
        "name": "抖音热点",
        "type": DataSourceType.HOTLIST,
        "priority": 8,
        "config": {
            "url": "https://www.douyin.com/discover",
            "method": "GET",
            "use_playwright": True,
            "timeout": 30000,
            "wait_for_selector": ".hot-list-item",
            "parse_type": "css",
            "parse_rules": {
                "container": ".hot-list-item",
                "title": ".title",
                "heat": ".heat-value",
            },
        },
    },
    {
        "name": "B站热门",
        "type": DataSourceType.HOTLIST,
        "priority": 6,
        "config": {
            "url": "https://api.bilibili.com/x/web-interface/ranking/index",
            "method": "GET",
            "parse_type": "json",
            "parse_rules": {
                "container": "data.list",
                "title": "title",
                "link": "url",
                "author": "owner.name",
                "likes": "stat.like",
            },
        },
    },
]


async def seed_data_sources(db: AsyncSession) -> None:
    """插入种子数据源"""

    # 创建热榜组
    hotlist_group = SourceGroup(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="热榜组",
        collect_interval=5,
        is_active=True,
    )
    db.add(hotlist_group)

    # 创建微博 KOL 组
    kol_group = SourceGroup(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        name="微博KOL组",
        collect_interval=30,
        is_active=True,
    )
    db.add(kol_group)

    # 插入热榜数据源
    for i, source_data in enumerate(HOTLIST_SOURCES):
        source = DataSource(
            id=uuid.UUID(f"00000000-0000-0000-0000-{str(i+1).zfill(12)}"),
            group_id=hotlist_group.id,
            name=source_data["name"],
            type=source_data["type"],
            collector_type=CollectorType.CONFIGURABLE,
            config=source_data["config"],
            priority=source_data["priority"],
            is_active=True,
            status=SourceStatus.ACTIVE,
        )
        db.add(source)

    # 插入微博 KOL 数据源
    for i, kol_data in enumerate(WEIBO_KOL_ACCOUNTS):
        source = DataSource(
            id=uuid.UUID(f"00000000-0000-0001-0000-{str(i+1).zfill(12)}"),
            group_id=kol_group.id,
            name=kol_data["name"],
            type=DataSourceType.ACCOUNT,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": f"https://weibo.com/u/{kol_data['uid']}",
                "method": "GET",
                "use_playwright": True,
                "timeout": 30000,
                "wait_for_selector": ".WB_feed_type",
                "parse_type": "css",
                "parse_rules": {
                    "container": ".WB_feed_type",
                    "title": ".WB_text",
                    "author": ".WB_feed_author .W_fb",
                },
                "uid": kol_data["uid"],
            },
            priority=kol_data["priority"],
            is_active=True,
            status=SourceStatus.ACTIVE,
        )
        db.add(source)

    await db.commit()
    print(f"Seeded {len(HOTLIST_SOURCES)} hotlist sources")
    print(f"Seeded {len(WEIBO_KOL_ACCOUNTS)} weibo KOL sources")


async def main() -> None:
    """主函数"""
    await db_manager.initialize()
    async with db_manager.session() as session:
        await seed_data_sources(session)
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())