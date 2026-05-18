"""
User Service Redis Client
"""
import redis.asyncio as redis
from typing import Optional

from .config import settings


class RedisManager:
    """Redis connection manager"""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        if self._redis is None:
            self._redis = await redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
        return self._redis
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        r = await self.connect()
        return await r.get(key)
    
    async def set(self, key: str, value: str, expire: int = None):
        """Set value in Redis"""
        r = await self.connect()
        await r.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        """Delete key from Redis"""
        r = await self.connect()
        await r.delete(key)
    
    async def incr(self, key: str) -> int:
        """Increment value"""
        r = await self.connect()
        return await r.incr(key)
    
    async def expire(self, key: str, seconds: int):
        """Set expiration"""
        r = await self.connect()
        await r.expire(key, seconds)


_redis_manager = None


def get_redis_manager() -> RedisManager:
    """Get or create Redis manager singleton"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


redis_manager = get_redis_manager()
