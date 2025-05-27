"""Redis cache configuration and utilities."""

import json
from typing import Any

import redis.asyncio as redis

from .config import settings


class CacheService:
    """Redis cache service."""

    def __init__(self):
        self.redis_client: redis.Redis | None = None

    async def connect(self):
        """Connect to Redis."""
        self.redis_client = redis.from_url(settings.redis_url)

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self.redis_client:
            return None

        value = await self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, expire: int = 3600):
        """Set value in cache with expiration."""
        if not self.redis_client:
            return False

        return await self.redis_client.set(key, json.dumps(value), ex=expire)

    async def delete(self, key: str):
        """Delete key from cache."""
        if not self.redis_client:
            return False

        return await self.redis_client.delete(key)


# Global cache instance
cache = CacheService()
