"""
Cookie管理 CLI
支持添加、查看、删除Cookie
"""
import asyncio
import json
import uuid
import click
from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy import select

from app.storage import db_manager
from app.storage.models import CookieEntry
from app.anti_crawl.cookie_pool import cookie_pool


@click.group()
def cli():
    """Cookie池管理"""
    pass


@cli.command("add")
@click.option("--source-id", required=True, help="数据源ID")
@click.option("--cookie", required=True, help="Cookie字符串或JSON文件路径")
@click.option("--name", default=None, help="Cookie名称")
@click.option("--expires-days", default=None, type=int, help="有效期(天)")
def add_cookie(source_id: str, cookie: str, name: str, expires_days: int):
    """添加Cookie"""
    async def _add():
        await db_manager.initialize()

        # 解析Cookie
        try:
            if cookie.startswith("{"):
                cookies = json.loads(cookie)
            elif cookie.endswith(".json"):
                with open(cookie, "r") as f:
                    cookies = json.load(f)
            else:
                # 解析Cookie字符串格式: key=value; key2=value2
                cookies = {}
                for item in cookie.split(";"):
                    item = item.strip()
                    if "=" in item:
                        key, value = item.split("=", 1)
                        cookies[key.strip()] = value.strip()
        except Exception as e:
            print(f"❌ Cookie解析失败: {e}")
            await db_manager.close()
            return

        # 添加Cookie
        await cookie_pool.initialize()
        cookie_id = await cookie_pool.add_cookie(
            source_id=source_id,
            cookies=cookies,
            name=name,
            expires_days=expires_days
        )

        print(f"✅ Cookie添加成功")
        print(f"   ID: {cookie_id}")
        print(f"   数据源: {source_id}")
        print(f"   名称: {name or '未命名'}")
        print(f"   Cookie数量: {len(cookies)}")
        if expires_days:
            print(f"   有效期: {expires_days}天")

        await cookie_pool.close()
        await db_manager.close()

    asyncio.run(_add())


@cli.command("add-batch")
@click.option("--source-id", required=True, help="数据源ID")
@click.option("--file", required=True, help="JSON文件路径(包含多个Cookie)")
@click.option("--expires-days", default=None, type=int, help="有效期(天)")
def add_batch(source_id: str, file: str, expires_days: int):
    """批量添加Cookie"""
    async def _add():
        await db_manager.initialize()

        try:
            with open(file, "r") as f:
                data = json.load(f)
                cookies_list = data if isinstance(data, list) else [data]
        except Exception as e:
            print(f"❌ 文件读取失败: {e}")
            await db_manager.close()
            return

        await cookie_pool.initialize()
        ids = await cookie_pool.add_cookies_batch(
            source_id=source_id,
            cookies_list=cookies_list,
            expires_days=expires_days
        )

        print(f"✅ 批量添加成功，共{len(ids)}个Cookie")
        for i, id in enumerate(ids):
            print(f"   [{i+1}] {id}")

        await cookie_pool.close()
        await db_manager.close()

    asyncio.run(_add())


@cli.command("list")
@click.option("--source-id", default=None, help="过滤数据源ID")
@click.option("--status", default=None, help="过滤状态: active/invalid/expired")
def list_cookies(source_id: str, status: str):
    """列出Cookie"""
    async def _list():
        await db_manager.initialize()

        async with db_manager.session() as session:
            query = select(CookieEntry).order_by(CookieEntry.created_at.desc())
            if source_id:
                query = query.where(CookieEntry.source_id == uuid.UUID(source_id))
            if status:
                query = query.where(CookieEntry.status == status)

            result = await session.execute(query)
            cookies = result.scalars().all()

            if not cookies:
                print("暂无Cookie")
                await db_manager.close()
                return

            print("\nCookie池列表:")
            print("-" * 80)
            for c in cookies:
                status_icon = {"active": "✓", "invalid": "✗", "expired": "⏰"}.get(c.status, "?")
                expires = c.expires_at.strftime("%Y-%m-%d") if c.expires_at else "永久"
                success_rate = c.success_rate() if c.use_count > 0 else "N/A"
                print(f"  [{status_icon}] {c.id} | {c.name or '未命名'} | {c.status}")
                print(f"       数据源: {c.source_id}")
                print(f"       使用: {c.use_count}次 | 成功: {c.success_count} | 成功率: {success_rate:.0%}")
                print(f"       过期: {expires} | 添加: {c.created_at.strftime('%Y-%m-%d')}")

        await db_manager.close()

    asyncio.run(_list())


@cli.command("stats")
@click.option("--source-id", required=True, help="数据源ID")
def stats(source_id: str):
    """查看统计"""
    async def _stats():
        await db_manager.initialize()
        await cookie_pool.initialize()

        stats = await cookie_pool.get_stats(source_id)
        print(f"\nCookie池统计 ({source_id}):")
        print("-" * 40)
        print(f"  总数: {stats['total']}")
        print(f"  可用: {stats['active']}")
        print(f"  失效: {stats['invalid']}")
        print(f"  过期: {stats['expired']}")
        print(f"  总使用: {stats['total_uses']}次")
        print(f"  总成功: {stats['total_success']}次")

        await cookie_pool.close()
        await db_manager.close()

    asyncio.run(_stats())


@cli.command("invalidate")
@click.option("--id", required=True, help="Cookie ID")
def invalidate(id: str):
    """失效Cookie"""
    async def _invalidate():
        await db_manager.initialize()
        await cookie_pool.initialize()

        result = await cookie_pool.invalidate_cookie(uuid.UUID(id))
        if result:
            print(f"✅ Cookie已失效: {id}")
        else:
            print(f"❌ Cookie不存在: {id}")

        await cookie_pool.close()
        await db_manager.close()

    asyncio.run(_invalidate())


@cli.command("delete")
@click.option("--id", required=True, help="Cookie ID")
def delete(id: str):
    """删除Cookie"""
    async def _delete():
        await db_manager.initialize()
        await cookie_pool.initialize()

        result = await cookie_pool.delete_cookie(uuid.UUID(id))
        if result:
            print(f"✅ Cookie已删除: {id}")
        else:
            print(f"❌ Cookie不存在: {id}")

        await cookie_pool.close()
        await db_manager.close()

    asyncio.run(_delete())


@cli.command("cleanup")
@click.option("--expired/--no-expired", default=True, help="清理过期Cookie")
@click.option("--invalid-days", default=30, type=int, help="清理失效超过N天的Cookie")
def cleanup(expired: bool, invalid_days: int):
    """清理Cookie"""
    async def _cleanup():
        await db_manager.initialize()
        await cookie_pool.initialize()

        total = 0
        if expired:
            n = await cookie_pool.cleanup_expired()
            total += n
            print(f"过期Cookie: {n}个")

        n = await cookie_pool.cleanup_invalid(max_age_days=invalid_days)
        total += n
        print(f"失效Cookie(>{invalid_days}天): {n}个")

        print(f"\n✅ 共清理: {total}个Cookie")

        await cookie_pool.close()
        await db_manager.close()

    asyncio.run(_cleanup())


if __name__ == "__main__":
    cli()