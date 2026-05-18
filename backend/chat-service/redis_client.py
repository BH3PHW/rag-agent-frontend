"""
Chat Service Redis Client
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
    
    async def get(self, key: str) -> Optional[str]:
        r = await self.connect()
        return await r.get(key)
    
    async def set(self, key: str, value: str, expire: int = None):
        r = await self.connect()
        await r.set(key, value, ex=expire)
    
    async def publish(self, channel: str, message: str):
        r = await self.connect()
        await r.publish(channel, message)


_redis_manager = None


def get_redis_manager() -> RedisManager:
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


redis_manager = get_redis_manager()
