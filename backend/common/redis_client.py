"""
Redis connection and utilities
"""
import json
from typing import Optional, Any
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from common.config import settings


class RedisManager:
    """Redis manager for async operations"""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        if self._redis is None:
            self._redis = await redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            return await self._redis.get(key)
        except RedisError:
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        expire: Optional[int] = None
    ) -> bool:
        """Set key-value with optional expiration"""
        try:
            if expire:
                await self._redis.setex(key, expire, value)
            else:
                await self._redis.set(key, value)
            return True
        except RedisError:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            await self._redis.delete(key)
            return True
        except RedisError:
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """Set JSON value"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return await self.set(key, json_str, expire)
        except (TypeError, json.JSONEncodeError):
            return False
    
    async def publish(self, channel: str, message: Any) -> bool:
        """Publish message to channel"""
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message, ensure_ascii=False)
            await self._redis.publish(channel, message)
            return True
        except RedisError:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self._redis.exists(key) > 0
        except RedisError:
            return False
    
    async def incr(self, key: str) -> Optional[int]:
        """Increment counter"""
        try:
            return await self._redis.incr(key)
        except RedisError:
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        try:
            return await self._redis.expire(key, seconds)
        except RedisError:
            return False


# Global Redis manager instance
redis_manager = RedisManager()


async def get_redis() -> Redis:
    """Get Redis connection"""
    return await redis_manager.connect()


# Cache decorators
def cache(expire: int = 3600):
    """Simple cache decorator for async functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and args
            cache_key = f"cache:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached = await redis_manager.get_json(cache_key)
            if cached is not None:
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await redis_manager.set_json(cache_key, result, expire)
            
            return result
        return wrapper
    return decorator
