"""
Analytics Service Redis Client
"""
import redis.asyncio as redis
from typing import Optional

from .config import settings


class RedisManager:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        if self._redis is None:
            self._redis = await redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
        return self._redis

    async def disconnect(self):
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def zadd(self, key: str, mapping: dict, expire: int = None):
        r = await self.connect()
        await r.zadd(key, mapping)
        if expire:
            await r.expire(key, expire)

    async def zincrby(self, key: str, member: str, amount: float):
        r = await self.connect()
        return await r.zincrby(key, amount, member)

    async def zrevrange(self, key: str, start: int, end: int, withscores: bool = False):
        r = await self.connect()
        return await r.zrevrange(key, start, end, withscores=withscores)


_redis_manager = None


def get_redis_manager() -> RedisManager:
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


redis_manager = get_redis_manager()
