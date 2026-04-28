"""
数据源配置脚本
通过数据库直接添加数据源分组和数据源
"""
import asyncio
import uuid
import sys
import os
from datetime import datetime

# 添加 app 目录到 Python 路径
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.storage.models import (
    Base, SourceGroup, DataSource,
    DataSourceType, CollectorType, SourceStatus
)


# 数据库连接
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector")


async def add_example_sources():
    """添加示例数据源配置"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ========== 1. 创建数据源分组 ==========

        # 热榜分组（5分钟采集一次）
        hotlist_group = SourceGroup(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="热榜数据源",
            collect_interval=5,  # 分钟
            is_active=True
        )

        # 社交账号分组（30分钟采集一次）
        social_group = SourceGroup(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            name="社交账号",
            collect_interval=30,
            is_active=True
        )

        # 短视频分组（30分钟采集一次）
        video_group = SourceGroup(
            id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
            name="短视频热点",
            collect_interval=30,
            is_active=True
        )

        session.add_all([hotlist_group, social_group, video_group])
        await session.commit()

        # ========== 2. 创建热榜数据源 ==========

        # 微博热搜（CSS解析）
        weibo_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
            group_id=hotlist_group.id,
            name="微博热搜",
            type=DataSourceType.HOTLIST,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://weibo.com/ajax/side/hotSearch",
                "method": "GET",
                "parse_type": "json",  # JSON API
                "parse_rules": {
                    "container": "data.realtime",  # JSON路径
                    "title": "note",
                    "rank": "rank",
                    "heat": "num",
                    "link": {"template": "https://s.weibo.com/weibo?q={word}"},
                    "word": "word"  # 用于构建链接
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                    "Referer": "https://weibo.com"
                }
            },
            priority=9,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        # 知乎热榜（JSON API）
        zhihu_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000002"),
            group_id=hotlist_group.id,
            name="知乎热榜",
            type=DataSourceType.HOTLIST,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
                "method": "GET",
                "parse_type": "json",
                "parse_rules": {
                    "container": "data",
                    "title": "target.title",
                    "heat": "detail_text",
                    "link": "target.url",
                    "excerpt": "target.excerpt"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                    "Referer": "https://www.zhihu.com"
                }
            },
            priority=8,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        # 百度热搜
        baidu_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000003"),
            group_id=hotlist_group.id,
            name="百度热搜",
            type=DataSourceType.HOTLIST,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://top.baidu.com/board?tab=realtime",
                "method": "GET",
                "parse_type": "css",
                "parse_rules": {
                    "container": ".content_1YWBm .item-wrap_2P2WB",
                    "title": ".content-title_3k3PR a",
                    "rank": ".index_1Ew5p",
                    "heat": ".hot-index_1Bl1a",
                    "link": ".content-title_3k3PR a@href"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
                }
            },
            priority=7,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        # 抖音热点
        douyin_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000004"),
            group_id=hotlist_group.id,
            name="抖音热点",
            type=DataSourceType.VIDEO,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://www.douyin.com/hot",
                "method": "GET",
                "parse_type": "css",
                "parse_rules": {
                    "container": ".hot-list-item",
                    "title": ".title",
                    "heat": ".heat-value",
                    "link": "a@href"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) Mobile/15E148",
                    "Referer": "https://www.douyin.com"
                },
                "use_playwright": True  # 需要动态渲染
            },
            priority=6,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        # B站热门
        bilibili_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000005"),
            group_id=hotlist_group.id,
            name="B站热门",
            type=DataSourceType.VIDEO,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://api.bilibili.com/x/web-interface/popular",
                "method": "GET",
                "parse_type": "json",
                "parse_rules": {
                    "container": "data.list",
                    "title": "title",
                    "author": "owner.name",
                    "likes": "stat.like",
                    "comments": "stat.view",
                    "link": {"template": "https://www.bilibili.com/video/{bvid}"},
                    "bvid": "bvid",
                    "cover": "pic"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                    "Referer": "https://www.bilibili.com"
                }
            },
            priority=5,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        session.add_all([weibo_hot, zhihu_hot, baidu_hot, douyin_hot, bilibili_hot])
        await session.commit()

        print("✅ 数据源配置完成!")
        print(f"  - 分组: 热榜数据源({hotlist_group.id})")
        print(f"  - 分组: 社交账号({social_group.id})")
        print(f"  - 分组: 短视频热点({video_group.id})")
        print(f"  - 数据源: 微博热搜、知乎热榜、百度热搜、抖音热点、B站热门")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(add_example_sources())