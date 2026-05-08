"""Redis cache wrapper"""
import json
from typing import Optional, Any

import redis.asyncio as aioredis

from app.core.config import settings


class CacheManager:
    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None

    async def initialize(self) -> None:
        self._client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        value = await self._client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if not self._client:
            return
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        await self._client.set(key, serialized, ex=ttl)

    async def get_with_ttl(self, key: str) -> tuple[Optional[Any], Optional[int]]:
        """Return (value, remaining_ttl_seconds). ttl=None means key absent."""
        if not self._client:
            return None, None
        pipe = self._client.pipeline()
        pipe.get(key)
        pipe.ttl(key)
        value, ttl = await pipe.execute()
        if value is None:
            return None, None
        try:
            return json.loads(value), ttl
        except (json.JSONDecodeError, TypeError):
            return value, ttl

    async def delete(self, key: str) -> None:
        if not self._client:
            return
        await self._client.delete(key)


cache_manager = CacheManager()
