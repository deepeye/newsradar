"""反爬防护模块 - 统一管理IP、UA、Cookie和频率控制"""
import random
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from uuid import UUID

from app.config import settings
from app.anti_crawl.ip_pool import ip_pool, ProxyInfo
from app.anti_crawl.cookie_pool import cookie_pool
from app.anti_crawl.rate_limiter import rate_limiter
from app.anti_crawl.ua_rotator import ua_rotator
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RequestContext:
    """请求上下文"""
    proxy: Optional[str] = None
    user_agent: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    cookie_id: Optional[UUID] = None  # 记录使用的Cookie ID


class AntiCrawlModule:
    """反爬防护统一入口"""

    def __init__(self):
        self.enabled = settings.anti_crawl.enabled
        self._initialized = False

    async def initialize(self) -> None:
        """初始化各子模块"""
        if not self.enabled or self._initialized:
            return

        await ip_pool.initialize()
        await cookie_pool.initialize()
        await rate_limiter.initialize()
        self._initialized = True
        logger.info("anti_crawl_initialized")

    async def close(self) -> None:
        """关闭各子模块"""
        if not self._initialized:
            return

        await ip_pool.close()
        await cookie_pool.close()
        await rate_limiter.close()
        self._initialized = False
        logger.info("anti_crawl_closed")

    async def get_context(self, source_id: str, platform: Optional[str] = None) -> RequestContext:
        """获取请求上下文（支持Cookie轮换，X平台共享Cookie）"""
        if not self.enabled:
            return RequestContext()

        # 获取代理
        proxy = None
        proxy_info = await ip_pool.get_proxy()
        if proxy_info:
            proxy = proxy_info.to_url()

        # 获取UA
        user_agent = ua_rotator.get_ua(platform)
        headers = ua_rotator.get_ua_with_headers(platform)

        # 获取Cookie（X平台共享，其他平台按source_id）
        cookies = None
        cookie_id = None
        cookie_data, cookie_id = await cookie_pool.get_cookie(source_id, platform=platform)
        if cookie_data:
            cookies = cookie_data

        return RequestContext(
            proxy=proxy,
            user_agent=user_agent,
            cookies=cookies,
            headers=headers,
            cookie_id=cookie_id
        )

    async def report_success(
        self,
        source_id: str,
        cookie_id: Optional[UUID] = None,
        proxy: Optional[str] = None
    ) -> None:
        """报告请求成功"""
        if not self.enabled:
            return

        if proxy:
            await ip_pool.report_success(proxy)

        if cookie_id:
            await cookie_pool.report_success(cookie_id)

        await rate_limiter.record_success(source_id)
        logger.debug("request_success_reported", source_id=source_id, cookie_id=str(cookie_id) if cookie_id else None)

    async def report_failure(
        self,
        source_id: str,
        cookie_id: Optional[UUID] = None,
        proxy: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> None:
        """报告请求失败"""
        if not self.enabled:
            return

        if proxy:
            await ip_pool.report_failure(proxy)

        if cookie_id:
            # 401/403 可能是Cookie失效
            if status_code in [401, 403]:
                await cookie_pool.report_failure(cookie_id, invalidate=True)
            else:
                await cookie_pool.report_failure(cookie_id)

        await rate_limiter.record_failure(source_id, status_code)

        # 401/403 标记Cookie失效
        if status_code in [401, 403]:
            logger.warning("cookie_invalidated_by_status",
                          source_id=source_id,
                          cookie_id=str(cookie_id) if cookie_id else None,
                          status_code=status_code)

        logger.debug("request_failure_reported",
                    source_id=source_id,
                    status_code=status_code,
                    cookie_id=str(cookie_id) if cookie_id else None)

    async def get_delay(self, source_id: str) -> float:
        """获取请求延迟（秒）"""
        if not self.enabled:
            return 0.0

        delay = await rate_limiter.get_delay(source_id)
        # 添加随机扰动
        jitter = random.uniform(0, 0.5)
        return delay + jitter

    async def add_cookies(
        self,
        source_id: str,
        cookies: Dict[str, str],
        name: Optional[str] = None,
        expires_days: Optional[int] = None,
        platform: Optional[str] = None
    ) -> UUID:
        """添加Cookie到池"""
        return await cookie_pool.add_cookie(source_id, cookies, name, expires_days, platform=platform)

    async def add_cookies_batch(
        self,
        source_id: str,
        cookies_list: List[Dict[str, str]],
        expires_days: Optional[int] = None,
        platform: Optional[str] = None
    ) -> List[UUID]:
        """批量添加Cookie"""
        return await cookie_pool.add_cookies_batch(source_id, cookies_list, expires_days, platform=platform)

    async def invalidate_cookies(self, source_id: str) -> int:
        """失效某个数据源的所有Cookie"""
        return await cookie_pool.invalidate_source_cookies(source_id)

    async def health_check(self) -> Dict[str, int]:
        """健康检查"""
        recovered_proxies = await ip_pool.health_check()
        cleaned_cookies = await cookie_pool.cleanup_expired()

        return {
            "recovered_proxies": recovered_proxies,
            "cleaned_cookies": cleaned_cookies,
        }


# 全局实例
anti_crawl = AntiCrawlModule()