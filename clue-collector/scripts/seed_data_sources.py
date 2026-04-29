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

# X (Twitter) KOL 账号
X_KOL_ACCOUNTS = [
    {
        "name": "Elon Musk",
        "handle": "elonmusk",
        "priority": 10,
    },
    {
        "name": "华尔街日报中文网",
        "handle": "ChineseWSJ",
        "priority": 9,
    },
    {
        "name": "Donald J. Trump",
        "handle": "realDonaldTrump",
        "priority": 10,
    },
    {
        "name": "Bloomberg",
        "handle": "business",
        "priority": 9,
    },
    {
        "name": "BBC News",
        "handle": "BBCWorld",
        "priority": 9,
    },
    {
        "name": "CNN",
        "handle": "CNN",
        "priority": 9,
    },
]

# 热榜数据源
HOTLIST_SOURCES = [
    {
        "name": "百度热搜",
        "type": DataSourceType.HOTLIST,
        "priority": 9,
        "config": {
            "url": "https://top.baidu.com/board?tab=realtime",
            "method": "GET",
            "parse_type": "css",
            "parse_rules": {
                "container": ".container-bg .content_1YWBm",
                "title": ".title_dIF3B",
                "heat": ".hot-index_1Bl1a",
                "link": "a@href",
            },
        },
    },
    {
        "name": "知乎热榜",
        "type": DataSourceType.HOTLIST,
        "priority": 9,
        "config": {
            "url": "https://www.zhihu.com/hot",
            "method": "GET",
            "use_playwright": True,
            "timeout": 30000,
            "wait_for_selector": ".HotList-item",
            "parse_type": "css",
            "parse_rules": {
                "container": ".HotList-item",
                "title": ".HotItem-title",
                "heat": ".HotItem-metrics",
                "link": "a@href",
            },
        },
    },
    {
        "name": "微博热搜",
        "type": DataSourceType.HOTLIST,
        "priority": 9,
        "config": {
            "url": "https://weibo.com/hot/search",
            "method": "GET",
            "use_playwright": True,
            "timeout": 30000,
            "wait_for_selector": ".search-card",
            "parse_type": "css",
            "parse_rules": {
                "container": ".card-wrap",
                "title": ".card-name",
                "heat": ".card-num",
                "link": "a@href",
            },
        },
    },
    {
        "name": "抖音热榜",
        "type": DataSourceType.HOTLIST,
        "priority": 9,
        "config": {
            "url": "https://www.douyin.com/hot",
            "method": "GET",
            "use_playwright": True,
            "timeout": 30000,
            "wait_for_selector": ".hot-list-item",
            "parse_type": "css",
            "parse_rules": {
                "container": ".hot-list-item",
                "title": ".title",
                "heat": ".heat-value",
                "link": "a@href",
            },
        },
    },
    {
        "name": "B站热搜",
        "type": DataSourceType.HOTLIST,
        "priority": 8,
        "config": {
            "url": "https://www.bilibili.com/v/popular/rank/all",
            "method": "GET",
            "use_playwright": True,
            "timeout": 30000,
            "wait_for_selector": ".rank-item",
            "parse_type": "css",
            "parse_rules": {
                "container": ".rank-item",
                "title": ".title",
                "heat": ".data-box",
                "link": "a@href",
            },
        },
    },
    {
        "name": "快手热榜",
        "type": DataSourceType.HOTLIST,
        "priority": 8,
        "config": {
            "url": "https://tophub.today/n/MZd7PrPerO",
            "method": "GET",
            "parse_type": "css",
            "parse_rules": {
                "container": ".tbody tr",
                "title": ".title a",
                "heat": ".heat",
                "link": ".title a@href",
            },
        },
    },
    {
        "name": "头条热榜",
        "type": DataSourceType.HOTLIST,
        "priority": 8,
        "config": {
            "url": "https://tophub.today/n/x9ozB4KoXb",
            "method": "GET",
            "parse_type": "css",
            "parse_rules": {
                "container": ".tbody tr",
                "title": ".title a",
                "heat": ".heat",
                "link": ".title a@href",
            },
        },
    },
    {
        "name": "微信热文榜",
        "type": DataSourceType.HOTLIST,
        "priority": 7,
        "config": {
            "url": "https://tophub.today/n/WnBe01o371",
            "method": "GET",
            "parse_type": "css",
            "parse_rules": {
                "container": ".tbody tr",
                "title": ".title a",
                "heat": ".heat",
                "link": ".title a@href",
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
    weibo_group = SourceGroup(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        name="微博KOL组",
        collect_interval=30,
        is_active=True,
    )
    db.add(weibo_group)

    # 创建 X (Twitter) KOL 组
    x_group = SourceGroup(
        id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        name="X KOL组",
        collect_interval=30,
        is_active=True,
    )
    db.add(x_group)

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
            group_id=weibo_group.id,
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

    # 插入 X (Twitter) KOL 数据源
    for i, kol_data in enumerate(X_KOL_ACCOUNTS):
        source = DataSource(
            id=uuid.UUID(f"00000000-0000-0002-0000-{str(i+1).zfill(12)}"),
            group_id=x_group.id,
            name=kol_data["name"],
            type=DataSourceType.ACCOUNT,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": f"https://x.com/{kol_data['handle']}",
                "method": "GET",
                "use_playwright": True,
                "timeout": 60000,
                "wait_for_selector": "[data-testid='tweet']",
                "parse_type": "css",
                "parse_rules": {
                    "container": "[data-testid='tweet']",
                    "title": "[data-testid='tweetText']",
                    "author": "[data-testid='User-Name']",
                    "time": "time",
                },
                "handle": kol_data["handle"],
                "platform": "x",
            },
            priority=kol_data["priority"],
            is_active=True,
            status=SourceStatus.ACTIVE,
        )
        db.add(source)

    await db.commit()
    print(f"Seeded {len(HOTLIST_SOURCES)} hotlist sources")
    print(f"Seeded {len(WEIBO_KOL_ACCOUNTS)} weibo KOL sources")
    print(f"Seeded {len(X_KOL_ACCOUNTS)} X KOL sources")


async def main() -> None:
    """主函数"""
    await db_manager.initialize()
    async with db_manager.session() as session:
        await seed_data_sources(session)
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())