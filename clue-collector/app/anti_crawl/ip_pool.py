"""IP轮换池"""
import random
import time
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime

import redis.asyncio as redis

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProxyInfo:
    """代理信息"""
    host: str
    port: int
    type: str = "http"  # http, https, socks5
    username: Optional[str] = None
    password: Optional[str] = None
    last_used: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0
    is_available: bool = True

    def to_url(self) -> str:
        """转换为代理URL"""
        if self.username and self.password:
            return f"{self.type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.type}://{self.host}:{self.port}"

    def score(self) -> float:
        """计算代理评分"""
        if self.success_count + self.failure_count == 0:
            return 0.5
        return self.success_count / (self.success_count + self.failure_count)


class IPPool:
    """IP轮换池"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.pool_key = "clue_collector:ip_pool"
        self.blocked_key = "clue_collector:ip_blocked"
        self.health_check_interval = 300  # 5分钟

    async def initialize(self) -> None:
        """初始化"""
        self.redis = redis.from_url(
            settings.redis.url,
            decode_responses=True
        )
        logger.info("ip_pool_initialized")

    async def close(self) -> None:
        """关闭"""
        if self.redis:
            await self.redis.close()

    async def add_proxy(self, proxy: ProxyInfo) -> bool:
        """添加代理"""
        proxy_data = {
            "host": proxy.host,
            "port": proxy.port,
            "type": proxy.type,
            "username": proxy.username or "",
            "password": proxy.password or "",
            "success_count": proxy.success_count,
            "failure_count": proxy.failure_count,
            "is_available": proxy.is_available,
        }

        await self.redis.hset(self.pool_key, proxy.to_url(), json.dumps(proxy_data))
        logger.debug("proxy_added", proxy=proxy.to_url())
        return True

    async def get_proxy(self) -> Optional[ProxyInfo]:
        """获取可用代理"""
        proxies = await self.redis.hgetall(self.pool_key)
        if not proxies:
            logger.warning("no_available_proxy")
            return None

        # 过滤可用代理，按评分排序
        available = []
        for url, data in proxies.items():
            proxy_dict = json.loads(data)
            if proxy_dict.get("is_available", True):
                proxy = ProxyInfo(
                    host=proxy_dict["host"],
                    port=int(proxy_dict["port"]),
                    type=proxy_dict.get("type", "http"),
                    username=proxy_dict.get("username"),
                    password=proxy_dict.get("password"),
                    success_count=int(proxy_dict.get("success_count", 0)),
                    failure_count=int(proxy_dict.get("failure_count", 0)),
                )
                available.append(proxy)

        if not available:
            return None

        # 按评分排序，随机选择高分代理
        available.sort(key=lambda p: p.score(), reverse=True)
        top_proxies = available[:min(5, len(available))]
        selected = random.choice(top_proxies)

        logger.debug("proxy_selected", proxy=selected.to_url(), score=selected.score())
        return selected

    async def report_success(self, proxy_url: str) -> None:
        """报告成功"""
        data = await self.redis.hget(self.pool_key, proxy_url)
        if data:
            proxy_dict = json.loads(data)
            proxy_dict["success_count"] = int(proxy_dict.get("success_count", 0)) + 1
            proxy_dict["last_used"] = time.time()
            await self.redis.hset(self.pool_key, proxy_url, json.dumps(proxy_dict))
            logger.debug("proxy_success", proxy=proxy_url)

    async def report_failure(self, proxy_url: str) -> None:
        """报告失败"""
        data = await self.redis.hget(self.pool_key, proxy_url)
        if data:
            proxy_dict = json.loads(data)
            proxy_dict["failure_count"] = int(proxy_dict.get("failure_count", 0)) + 1
            proxy_dict["last_used"] = time.time()

            # 连续3次失败标记不可用
            if proxy_dict["failure_count"] >= 3:
                proxy_dict["is_available"] = False
                await self.redis.hset(self.blocked_key, proxy_url, time.time())
                logger.warning("proxy_blocked", proxy=proxy_url, failures=proxy_dict["failure_count"])

            await self.redis.hset(self.pool_key, proxy_url, json.dumps(proxy_dict))

    async def health_check(self) -> int:
        """健康检查，恢复被封代理"""
        blocked = await self.redis.hgetall(self.blocked_key)
        recovered = 0

        current_time = time.time()
        for proxy_url, blocked_time in blocked.items():
            # 30分钟后尝试恢复
            if current_time - float(blocked_time) > 1800:
                data = await self.redis.hget(self.pool_key, proxy_url)
                if data:
                    proxy_dict = json.loads(data)
                    proxy_dict["is_available"] = True
                    proxy_dict["failure_count"] = 0
                    await self.redis.hset(self.pool_key, proxy_url, json.dumps(proxy_dict))
                    await self.redis.hdel(self.blocked_key, proxy_url)
                    recovered += 1
                    logger.info("proxy_recovered", proxy=proxy_url)

        if recovered > 0:
            logger.info("health_check_completed", recovered=recovered)

        return recovered

    async def load_from_config(self, config_path: str = None) -> int:
        """从配置加载代理"""
        # TODO: 从 proxy_providers.yaml 加载
        return 0


# 需要导入 json
import json

# 全局实例
ip_pool = IPPool()