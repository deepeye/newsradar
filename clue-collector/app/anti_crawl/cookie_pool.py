"""Cookie池管理 - 数据库存储，支持多Cookie轮换"""
import random
from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select, update, delete, func, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage import db_manager
from app.storage.models import CookieEntry, CookieStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CookiePool:
    """Cookie池 - 数据库存储，支持多Cookie轮换"""

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        """初始化"""
        self._initialized = True
        logger.info("cookie_pool_initialized")

    async def close(self) -> None:
        """关闭"""
        self._initialized = False
        logger.info("cookie_pool_closed")

    async def add_cookie(
        self,
        source_id: str,
        cookies: Dict[str, str],
        name: Optional[str] = None,
        expires_days: Optional[int] = None,
        platform: Optional[str] = None,
    ) -> UUID:
        """添加单个Cookie"""
        async with db_manager.session() as session:
            expires_at = None
            if expires_days:
                expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

            cookie_entry = CookieEntry(
                source_id=UUID(source_id),
                cookies=cookies,
                name=name,
                platform=platform,
                status="active",
                expires_at=expires_at
            )
            session.add(cookie_entry)
            await session.commit()

            logger.info("cookie_added",
                       cookie_id=str(cookie_entry.id),
                       source_id=source_id,
                       name=name,
                       expires_days=expires_days)
            return cookie_entry.id

    async def add_cookies_batch(
        self,
        source_id: str,
        cookies_list: List[Dict[str, str]],
        expires_days: Optional[int] = None,
        platform: Optional[str] = None
    ) -> List[UUID]:
        """批量添加Cookie"""
        ids = []
        for i, cookies in enumerate(cookies_list):
            cookie_id = await self.add_cookie(
                source_id=source_id,
                cookies=cookies,
                name=f"Cookie-{i+1}",
                expires_days=expires_days,
                platform=platform
            )
            ids.append(cookie_id)
        logger.info("cookies_batch_added", source_id=source_id, count=len(ids))
        return ids

    async def get_cookie(self, source_id: str, platform: Optional[str] = None) -> tuple[Optional[Dict[str, str]], Optional[UUID]]:
        """获取一个可用Cookie（轮换策略：随机选择 + 成功率优先）

        Returns: (cookies_dict, cookie_id) — cookie_id for reporting success/failure.
        When platform="x": share cookies across all X data sources.
        Otherwise: only find cookies bound to this source_id.
        """
        async with db_manager.session() as session:
            # X platform: share cookies across all X sources
            if platform == "x":
                result = await session.execute(
                    select(CookieEntry)
                    .where(CookieEntry.platform == "x")
                    .where(CookieEntry.status == "active")
                    .where(
                        (CookieEntry.expires_at == None) |
                        (CookieEntry.expires_at > datetime.now(timezone.utc))
                    )
                    .order_by(CookieEntry.success_count.desc(), CookieEntry.use_count.asc())
                )
            else:
                # Per-source lookup (weibo, etc.)
                result = await session.execute(
                    select(CookieEntry)
                    .where(CookieEntry.source_id == UUID(source_id))
                    .where(CookieEntry.status == "active")
                    .where(
                        (CookieEntry.expires_at == None) |
                        (CookieEntry.expires_at > datetime.now(timezone.utc))
                    )
                    .order_by(CookieEntry.success_count.desc(), CookieEntry.use_count.asc())
                )
            cookies = result.scalars().all()

            if not cookies:
                logger.debug("no_available_cookies", source_id=source_id, platform=platform)
                return None, None

            # Selection strategy: prefer "perfect" cookies, otherwise random from top 3
            perfect_cookies = [c for c in cookies if c.fail_count == 0 and c.use_count > 0]
            if perfect_cookies:
                selected = random.choice(perfect_cookies)
            else:
                selected = random.choice(cookies[:min(3, len(cookies))])

            # Update usage record
            await session.execute(
                update(CookieEntry)
                .where(CookieEntry.id == selected.id)
                .values(
                    use_count=selected.use_count + 1,
                    last_used_at=datetime.now(timezone.utc)
                )
            )
            await session.commit()

            logger.debug("cookie_selected",
                        cookie_id=str(selected.id),
                        source_id=source_id,
                        platform=platform,
                        cookie_source_id=str(selected.source_id),
                        use_count=selected.use_count)
            return selected.cookies, selected.id

    async def get_all_cookies(self, source_id: str) -> List[CookieEntry]:
        """获取数据源所有Cookie"""
        async with db_manager.session() as session:
            result = await session.execute(
                select(CookieEntry)
                .where(CookieEntry.source_id == UUID(source_id))
                .order_by(CookieEntry.created_at.desc())
            )
            return list(result.scalars().all())

    async def report_success(self, cookie_id: UUID) -> None:
        """报告Cookie使用成功"""
        async with db_manager.session() as session:
            await session.execute(
                update(CookieEntry)
                .where(CookieEntry.id == cookie_id)
                .values(
                    success_count=CookieEntry.success_count + 1,
                    last_success_at=datetime.now(timezone.utc),
                    status="active"
                )
            )
            await session.commit()
            logger.debug("cookie_success_reported", cookie_id=str(cookie_id))

    async def report_failure(self, cookie_id: UUID, invalidate: bool = False) -> None:
        """报告Cookie使用失败"""
        async with db_manager.session() as session:
            cookie = await session.execute(
                select(CookieEntry).where(CookieEntry.id == cookie_id)
            )
            entry = cookie.scalar_one_or_none()

            if not entry:
                return

            new_fail_count = entry.fail_count + 1
            # 连续3次失败标记为失效
            new_status = entry.status
            if new_fail_count >= 3 or invalidate:
                new_status = "invalid"
                logger.warning("cookie_marked_invalid",
                              cookie_id=str(cookie_id),
                              fail_count=new_fail_count)

            await session.execute(
                update(CookieEntry)
                .where(CookieEntry.id == cookie_id)
                .values(
                    fail_count=new_fail_count,
                    status=new_status
                )
            )
            await session.commit()

    async def invalidate_cookie(self, cookie_id: UUID) -> bool:
        """手动失效Cookie"""
        async with db_manager.session() as session:
            result = await session.execute(
                update(CookieEntry)
                .where(CookieEntry.id == cookie_id)
                .values(status="invalid")
            )
            await session.commit()
            logger.info("cookie_invalidated", cookie_id=str(cookie_id))
            return result.rowcount > 0

    async def invalidate_source_cookies(self, source_id: str) -> int:
        """失效某个数据源的所有Cookie"""
        async with db_manager.session() as session:
            result = await session.execute(
                update(CookieEntry)
                .where(CookieEntry.source_id == UUID(source_id))
                .where(CookieEntry.status == "active")
                .values(status="invalid")
            )
            await session.commit()
            logger.info("source_cookies_invalidated", source_id=source_id, count=result.rowcount)
            return result.rowcount

    async def delete_cookie(self, cookie_id: UUID) -> bool:
        """删除Cookie"""
        async with db_manager.session() as session:
            result = await session.execute(
                delete(CookieEntry).where(CookieEntry.id == cookie_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def get_available_sources(self) -> List[str]:
        """获取有可用Cookie的数据源列表"""
        async with db_manager.session() as session:
            result = await session.execute(
                select(CookieEntry.source_id)
                .where(CookieEntry.status == "active")
                .where(
                    (CookieEntry.expires_at == None) |
                    (CookieEntry.expires_at > datetime.now(timezone.utc))
                )
                .distinct()
            )
            return [str(row[0]) for row in result.all()]

    async def cleanup_expired(self) -> int:
        """清理过期Cookie"""
        async with db_manager.session() as session:
            result = await session.execute(
                update(CookieEntry)
                .where(CookieEntry.expires_at != None)
                .where(CookieEntry.expires_at < datetime.now(timezone.utc))
                .where(CookieEntry.status == "active")
                .values(status="expired")
            )
            await session.commit()
            cleaned = result.rowcount
            if cleaned > 0:
                logger.info("expired_cookies_cleaned", count=cleaned)
            return cleaned

    async def cleanup_invalid(self, max_age_days: int = 30) -> int:
        """清理失效超过一定时间的Cookie"""
        async with db_manager.session() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            result = await session.execute(
                delete(CookieEntry)
                .where(CookieEntry.status == "invalid")
                .where(CookieEntry.updated_at < cutoff)
            )
            await session.commit()
            cleaned = result.rowcount
            if cleaned > 0:
                logger.info("invalid_cookies_cleaned", count=cleaned)
            return cleaned

    async def get_stats(self, source_id: str) -> Dict:
        """获取Cookie池统计"""
        async with db_manager.session() as session:
            result = await session.execute(
                select(
                    func.count(CookieEntry.id).label("total"),
                    func.sum(func.cast(CookieEntry.status == "active", type_=Integer)).label("active"),
                    func.sum(func.cast(CookieEntry.status == "invalid", type_=Integer)).label("invalid"),
                    func.sum(func.cast(CookieEntry.status == "expired", type_=Integer)).label("expired"),
                    func.sum(CookieEntry.use_count).label("total_uses"),
                    func.sum(CookieEntry.success_count).label("total_success"),
                )
                .where(CookieEntry.source_id == UUID(source_id))
            )
            row = result.one()
            return {
                "total": row.total or 0,
                "active": row.active or 0,
                "invalid": row.invalid or 0,
                "expired": row.expired or 0,
                "total_uses": row.total_uses or 0,
                "total_success": row.total_success or 0,
            }


# 全局实例
cookie_pool = CookiePool()