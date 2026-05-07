"""
更新数据源配置脚本
将知乎、微博、抖音改为 TopHub 聚合页面，新增澎湃热榜
"""
import asyncio
import uuid
import sys
import os

sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector")


async def update_sources():
    """更新数据源配置"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ========== 更新现有数据源 ==========

        # 知乎热榜 - 改为 TopHub
        await session.execute(text("""
            UPDATE data_sources
            SET config = jsonb_set(
                config,
                '{url}',
                '"https://tophub.today/n/mproPpoq6O"'
            ),
            config = jsonb_set(
                config,
                '{parse_type}',
                '"css"'
            ),
            config = jsonb_set(
                config,
                '{parse_rules}',
                '{"container": "table tbody tr", "rank": "td:nth-child(1)", "title": "td:nth-child(3) a", "heat": "td:nth-child(3)", "link": "td:nth-child(3) a@href"}'
            ),
            config = jsonb_set(
                config,
                '{use_playwright}',
                'true'
            ),
            config = jsonb_set(
                config,
                '{wait_for_selector}',
                '"table tbody tr"'
            ),
            status = 'ACTIVE'
            WHERE name = '知乎热榜'
        """))

        # 微博热搜 - 改为 TopHub
        await session.execute(text("""
            UPDATE data_sources
            SET config = jsonb_set(
                config,
                '{url}',
                '"https://tophub.today/n/KqndgxeLl9"'
            ),
            config = jsonb_set(
                config,
                '{parse_type}',
                '"css"'
            ),
            config = jsonb_set(
                config,
                '{parse_rules}',
                '{"container": "table tbody tr", "rank": "td:nth-child(1)", "title": "td:nth-child(3) a", "heat": "td:nth-child(3)", "link": "td:nth-child(3) a@href"}'
            ),
            config = jsonb_set(
                config,
                '{use_playwright}',
                'true'
            ),
            config = jsonb_set(
                config,
                '{wait_for_selector}',
                '"table tbody tr"'
            ),
            status = 'ACTIVE'
            WHERE name = '微博热搜'
        """))

        # 抖音热点 - 改为 TopHub
        await session.execute(text("""
            UPDATE data_sources
            SET config = jsonb_set(
                config,
                '{url}',
                '"https://tophub.today/n/K7GdaMgdQy"'
            ),
            config = jsonb_set(
                config,
                '{parse_type}',
                '"css"'
            ),
            config = jsonb_set(
                config,
                '{parse_rules}',
                '{"container": "table tbody tr", "rank": "td:nth-child(1)", "title": "td:nth-child(3) a", "heat": "td:nth-child(3)", "link": "td:nth-child(3) a@href"}'
            ),
            config = jsonb_set(
                config,
                '{use_playwright}',
                'true'
            ),
            config = jsonb_set(
                config,
                '{wait_for_selector}',
                '"table tbody tr"'
            ),
            status = 'ACTIVE'
            WHERE name = '抖音热点'
        """))

        # ========== 新增澎湃热榜 ==========

        # 检查是否已存在
        result = await session.execute(text("SELECT id FROM data_sources WHERE name = '澎湃热榜'"))
        if result.fetchone() is None:
            await session.execute(text("""
                INSERT INTO data_sources (
                    id, group_id, name, type, collector_type, config, priority, is_active, status
                ) VALUES (
                    '10000000-0000-0000-0000-000000000007',
                    '00000000-0000-0000-0000-000000000001',
                    '澎湃热榜',
                    'hotlist',
                    'configurable',
                    '{"url": "https://tophub.today/n/wWmoO5Rd4E", "method": "GET", "parse_type": "css", "parse_rules": {"container": "table tbody tr", "rank": "td:nth-child(1)", "title": "td:nth-child(3) a", "heat": "td:nth-child(3)", "link": "td:nth-child(3) a@href"}, "headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}, "use_playwright": true, "wait_for_selector": "table tbody tr"}',
                    5,
                    true,
                    'ACTIVE'
                )
            """))

        await session.commit()
        print("✅ 数据源配置更新完成!")
        print("  - 知乎热榜: 改为 TopHub 聚合页面")
        print("  - 微博热搜: 改为 TopHub 聚合页面")
        print("  - 抖音热点: 改为 TopHub 聚合页面")
        print("  - 澎湃热榜: 新增")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(update_sources())