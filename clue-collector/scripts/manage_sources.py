"""
数据源管理 CLI
使用 click 提供命令行接口管理数据源配置
"""
import asyncio
import json
import uuid
import click
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.storage.models import (
    SourceGroup, DataSource,
    DataSourceType, CollectorType, SourceStatus
)


# 数据库连接
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector"


def get_session():
    """获取数据库会话"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False), engine


@click.group()
def cli():
    """线索采集服务 - 数据源管理"""
    pass


@cli.command("add-group")
@click.option("--name", required=True, help="分组名称")
@click.option("--interval", default=30, help="采集频率(分钟)")
@click.option("--active/--inactive", default=True, help="是否启用")
def add_group(name: str, interval: int, active: bool):
    """添加数据源分组"""
    async_session, engine = get_session()

    async def _add():
        async with async_session() as session:
            group = SourceGroup(
                name=name,
                collect_interval=interval,
                is_active=active
            )
            session.add(group)
            await session.commit()
            print(f"✅ 分组创建成功: {group.id}")
            print(f"   名称: {name}, 频率: {interval}分钟, 启用: {active}")
        await engine.dispose()

    asyncio.run(_add())


@cli.command("list-groups")
def list_groups():
    """列出所有分组"""
    async_session, engine = get_session()

    async def _list():
        async with async_session() as session:
            result = await session.execute(
                select(SourceGroup).order_by(SourceGroup.created_at)
            )
            groups = result.scalars().all()

            if not groups:
                print("暂无分组")
                return

            print("\n数据源分组列表:")
            print("-" * 60)
            for g in groups:
                status = "✓" if g.is_active else "✗"
                print(f"  [{status}] {g.id} | {g.name} | 频率:{g.collect_interval}分钟")
        await engine.dispose()

    asyncio.run(_list())


@cli.command("add-source")
@click.option("--group-id", required=True, help="分组ID")
@click.option("--name", required=True, help="数据源名称")
@click.option("--type", type=click.Choice(["hotlist", "account", "video", "custom"]),
              required=True, help="数据源类型")
@click.option("--collector", type=click.Choice(["configurable", "plugin"]),
              default="configurable", help="采集器类型")
@click.option("--config", required=True, help="采集配置(JSON字符串或文件路径)")
@click.option("--priority", default=5, help="优先级(1-10)")
@click.option("--active/--inactive", default=True, help="是否启用")
def add_source(group_id: str, name: str, type: str, collector: str,
               config: str, priority: int, active: bool):
    """添加数据源"""
    async_session, engine = get_session()

    # 解析配置
    try:
        if config.startswith("{") or config.startswith("["):
            config_dict = json.loads(config)
        else:
            with open(config, "r") as f:
                config_dict = json.load(f)
    except Exception as e:
        print(f"❌ 配置解析失败: {e}")
        return

    async def _add():
        async with async_session() as session:
            # 验证分组存在
            result = await session.execute(
                select(SourceGroup).where(SourceGroup.id == uuid.UUID(group_id))
            )
            group = result.scalar_one_or_none()
            if not group:
                print(f"❌ 分组不存在: {group_id}")
                return

            source = DataSource(
                group_id=uuid.UUID(group_id),
                name=name,
                type=DataSourceType(type),
                collector_type=CollectorType(collector),
                config=config_dict,
                priority=priority,
                is_active=active,
                status=SourceStatus.ACTIVE
            )
            session.add(source)
            await session.commit()
            print(f"✅ 数据源创建成功: {source.id}")
            print(f"   名称: {name}, 类型: {type}, 分组: {group.name}")
        await engine.dispose()

    asyncio.run(_add())


@cli.command("list-sources")
@click.option("--group-id", default=None, help="过滤分组ID")
def list_sources(group_id: Optional[str]):
    """列出数据源"""
    async_session, engine = get_session()

    async def _list():
        async with async_session() as session:
            query = select(DataSource).order_by(DataSource.priority.desc())
            if group_id:
                query = query.where(DataSource.group_id == uuid.UUID(group_id))

            result = await session.execute(query)
            sources = result.scalars().all()

            if not sources:
                print("暂无数据源")
                return

            print("\n数据源列表:")
            print("-" * 80)
            for s in sources:
                status = "✓" if s.is_active else "✗"
                st = s.status.value
                print(f"  [{status}] {s.id} | {s.name} | {s.type.value} | 优先级:{s.priority} | 状态:{st}")
                print(f"       配置: {json.dumps(s.config, ensure_ascii=False)[:50]}...")
        await engine.dispose()

    asyncio.run(_list())


@cli.command("delete-source")
@click.option("--id", required=True, help="数据源ID")
def delete_source(id: str):
    """删除数据源"""
    async_session, engine = get_session()

    async def _delete():
        async with async_session() as session:
            result = await session.execute(
                select(DataSource).where(DataSource.id == uuid.UUID(id))
            )
            source = result.scalar_one_or_none()
            if not source:
                print(f"❌ 数据源不存在: {id}")
                return

            await session.delete(source)
            await session.commit()
            print(f"✅ 数据源已删除: {source.name}")
        await engine.dispose()

    asyncio.run(_delete())


@cli.command("toggle-source")
@click.option("--id", required=True, help="数据源ID")
@click.option("--active/--inactive", required=True, help="启用或禁用")
def toggle_source(id: str, active: bool):
    """启用/禁用数据源"""
    async_session, engine = get_session()

    async def _toggle():
        async with async_session() as session:
            result = await session.execute(
                select(DataSource).where(DataSource.id == uuid.UUID(id))
            )
            source = result.scalar_one_or_none()
            if not source:
                print(f"❌ 数据源不存在: {id}")
                return

            source.is_active = active
            await session.commit()
            action = "启用" if active else "禁用"
            print(f"✅ 数据源已{action}: {source.name}")
        await engine.dispose()

    asyncio.run(_toggle())


@cli.command("example-configs")
def example_configs():
    """显示示例配置"""
    examples = {
        "微博热搜(JSON API)": {
            "url": "https://weibo.com/ajax/side/hotSearch",
            "method": "GET",
            "parse_type": "json",
            "parse_rules": {
                "container": "data.realtime",
                "title": "note",
                "rank": "rank",
                "heat": "num",
                "link": {"template": "https://s.weibo.com/weibo?q={word}"},
                "word": "word"
            },
            "headers": {
                "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0",
                "Referer": "https://weibo.com"
            }
        },
        "知乎热榜(JSON API)": {
            "url": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
            "method": "GET",
            "parse_type": "json",
            "parse_rules": {
                "container": "data",
                "title": "target.title",
                "heat": "detail_text",
                "link": "target.url"
            }
        },
        "CSS选择器示例": {
            "url": "https://example.com/hot",
            "method": "GET",
            "parse_type": "css",
            "parse_rules": {
                "container": ".hot-list li",
                "title": ".title",
                "rank": ".rank",
                "heat": ".heat",
                "link": "a@href"
            }
        },
        "需要动态渲染": {
            "url": "https://example.com",
            "method": "GET",
            "parse_type": "css",
            "parse_rules": {...},
            "use_playwright": True
        }
    }

    print("\n示例配置格式:")
    print("=" * 60)
    for name, config in examples.items():
        print(f"\n【{name}】")
        print(json.dumps(config, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli()