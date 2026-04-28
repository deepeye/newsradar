"""频率自适应控制器"""
import random
import time
from typing import Dict, Optional
from dataclasses import dataclass, field

import redis.asyncio as redis

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FrequencyState:
    """频率状态"""
    base_interval: float = 2.0
    current_interval: float = 2.0
    min_interval: float = 1.0
    max_interval: float = 10.0
    success_count: int = 0
    failure_count: int = 0
    last_request_time: Optional[float] = None
    is_degraded: bool = False


class RateLimiter:
    """频率自适应控制器"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.state_key = "clue_collector:rate_limiter"

    async def initialize(self) -> None:
        """初始化"""
        self.redis = redis.from_url(
            settings.redis.url,
            decode_responses=True
        )
        logger.info("rate_limiter_initialized")

    async def close(self) -> None:
        """关闭"""
        if self.redis:
            await self.redis.close()

    async def get_state(self, source_id: str) -> FrequencyState:
        """获取频率状态"""
        key = f"{self.state_key}:{source_id}"
        data = await self.redis.get(key)

        if data:
            state_dict = json.loads(data)
            return FrequencyState(**state_dict)

        # 默认状态
        return FrequencyState(
            base_interval=settings.anti_crawl.request_interval,
            min_interval=settings.anti_crawl.min_interval,
            max_interval=settings.anti_crawl.max_interval
        )

    async def save_state(self, source_id: str, state: FrequencyState) -> None:
        """保存频率状态"""
        key = f"{self.state_key}:{source_id}"
        state_dict = {
            "base_interval": state.base_interval,
            "current_interval": state.current_interval,
            "min_interval": state.min_interval,
            "max_interval": state.max_interval,
            "success_count": state.success_count,
            "failure_count": state.failure_count,
            "last_request_time": state.last_request_time,
            "is_degraded": state.is_degraded,
        }
        await self.redis.set(key, json.dumps(state_dict))

    async def get_delay(self, source_id: str) -> float:
        """获取请求延迟"""
        state = await self.get_state(source_id)

        # 检查上次请求时间
        if state.last_request_time:
            elapsed = time.time() - state.last_request_time
            if elapsed < state.current_interval:
                remaining = state.current_interval - elapsed
                logger.debug("rate_limit_wait", source_id=source_id, wait=remaining)
                return remaining

        # 添加随机扰动
        jitter = random.uniform(-0.3, 0.5)
        delay = state.current_interval + jitter
        delay = max(state.min_interval, min(delay, state.max_interval))

        return delay

    async def record_success(self, source_id: str) -> None:
        """记录成功"""
        state = await self.get_state(source_id)
        state.success_count += 1
        state.failure_count = 0
        state.last_request_time = time.time()

        # 成功5次后恢复频率
        if state.is_degraded and state.success_count >= 5:
            state.current_interval = state.base_interval
            state.is_degraded = False
            logger.info("rate_restored", source_id=source_id)

        await self.save_state(source_id, state)

    async def record_failure(self, source_id: str, status_code: int = None) -> None:
        """记录失败"""
        state = await self.get_state(source_id)
        state.failure_count += 1
        state.success_count = 0
        state.last_request_time = time.time()

        # 遇到429/403降频
        if status_code in [429, 403]:
            state.current_interval = min(
                state.current_interval * 1.5,
                state.max_interval
            )
            state.is_degraded = True
            logger.warning("rate_degraded",
                          source_id=source_id,
                          new_interval=state.current_interval)

        await self.save_state(source_id, state)

    async def reset(self, source_id: str) -> None:
        """重置频率"""
        key = f"{self.state_key}:{source_id}"
        await self.redis.delete(key)
        logger.info("rate_reset", source_id=source_id)


# 需要导入 json
import json

# 全局实例
rate_limiter = RateLimiter()