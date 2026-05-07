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
            collect_interval=5,
            is_active=True
        )

        # 短视频分组（30分钟采集一次）
        video_group = SourceGroup(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            name="短视频热点",
            collect_interval=30,
            is_active=True
        )

        # 新闻资讯分组（10分钟采集一次）
        news_group = SourceGroup(
            id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
            name="新闻资讯",
            collect_interval=10,
            is_active=True
        )

        session.add_all([hotlist_group, video_group, news_group])
        await session.commit()

        # ========== 2. 创建数据源 ==========

        # 百度热搜（JSON API）
        baidu_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
            group_id=hotlist_group.id,
            name="百度热搜",
            type=DataSourceType.HOTLIST,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://top.baidu.com/api/board?platform=pc&tab=realtime",
                "method": "GET",
                "parse_type": "json",
                "parse_rules": {
                    "container": "data.cards.0.content",
                    "title": "word",
                    "rank": "index",
                    "heat": "hotScore",
                    "link": "url",
                    "desc": "desc"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                    "Referer": "https://top.baidu.com"
                }
            },
            priority=9,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        # 头条热榜（JSON API）
        toutiao_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000002"),
            group_id=hotlist_group.id,
            name="头条热榜",
            type=DataSourceType.HOTLIST,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
                "method": "GET",
                "parse_type": "json",
                "parse_rules": {
                    "container": "data",
                    "title": "Title",
                    "heat": "HotValue",
                    "link": "Url"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                    "Referer": "https://www.toutiao.com"
                }
            },
            priority=8,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        # 微博热搜（Playwright动态渲染）
        weibo_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000003"),
            group_id=hotlist_group.id,
            name="微博热搜",
            type=DataSourceType.HOTLIST,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://weibo.com/hot/search",
                "method": "GET",
                "parse_type": "css",
                "parse_rules": {
                    "container": "[class*='list_a'] [class*='item_']",
                    "title": "[class*='text_'] a",
                    "rank": "[class*='rank_']",
                    "heat": "[class*='number_']",
                    "link": "a@href"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                    "Referer": "https://weibo.com"
                },
                "use_playwright": True,
                "wait_for_selector": "[class*='list_a']"
            },
            priority=7,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        # 知乎热榜（Playwright动态渲染）
        zhihu_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000004"),
            group_id=hotlist_group.id,
            name="知乎热榜",
            type=DataSourceType.HOTLIST,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://www.zhihu.com/hot",
                "method": "GET",
                "parse_type": "css",
                "parse_rules": {
                    "container": "[class*='HotItem']",
                    "title": "[class*='Title']",
                    "heat": "[class*='HotMetric']",
                    "rank": "[class*='HotItem-index']",
                    "link": "a@href"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                    "Referer": "https://www.zhihu.com"
                },
                "use_playwright": True,
                "wait_for_selector": "[class*='HotItem']"
            },
            priority=6,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        # B站热门（JSON API）
        bilibili_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000005"),
            group_id=video_group.id,
            name="B站热门",
            type=DataSourceType.VIDEO,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://api.bilibili.com/x/web-interface/popular?pn=1&ps=20",
                "method": "GET",
                "parse_type": "json",
                "parse_rules": {
                    "container": "data.list",
                    "title": "title",
                    "author": "owner.name",
                    "heat": "stat.view",
                    "link": {"template": "https://www.bilibili.com/video/{bvid}"},
                    "bvid": "bvid",
                    "cover": "pic"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                    "Referer": "https://www.bilibili.com"
                }
            },
            priority=8,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        # 抖音热点（Playwright动态渲染）
        douyin_hot = DataSource(
            id=uuid.UUID("10000000-0000-0000-0000-000000000006"),
            group_id=video_group.id,
            name="抖音热点",
            type=DataSourceType.VIDEO,
            collector_type=CollectorType.CONFIGURABLE,
            config={
                "url": "https://www.douyin.com/hot",
                "method": "GET",
                "parse_type": "css",
                "parse_rules": {
                    "container": "[class*='hot-item']",
                    "title": "[class*='title']",
                    "heat": "[class*='hot-value']",
                    "link": "a@href"
                },
                "headers": {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) Mobile/15E148",
                    "Referer": "https://www.douyin.com"
                },
                "use_playwright": True,
                "wait_for_selector": "[class*='hot-item']"
            },
            priority=5,
            is_active=True,
            status=SourceStatus.ACTIVE
        )

        session.add_all([baidu_hot, toutiao_hot, weibo_hot, zhihu_hot, bilibili_hot, douyin_hot])
        await session.commit()

        print("✅ 数据源配置完成!")
        print(f"  - 分组: 热榜数据源({hotlist_group.id})")
        print(f"  - 分组: 短视频热点({video_group.id})")
        print(f"  - 分组: 新闻资讯({news_group.id})")
        print(f"  - 数据源: 百度热搜、头条热榜、微博热搜、知乎热榜、B站热门、抖音热点")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(add_example_sources())
