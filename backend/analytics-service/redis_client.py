"""
Analytics-Service Service Redis Client
使用common.redis_client模块
"""
import sys
from pathlib import Path

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

# 尝试使用common.redis_client
try:
    from common.redis_client import RedisManager, redis_manager as common_redis_manager
    from .config import settings
    
    # 创建Analytics-Service Service专用的Redis管理器
    _redis_manager = None
    
    def get_redis_manager() -> RedisManager:
        """获取Redis管理器"""
        global _redis_manager
        if _redis_manager is None:
            _redis_manager = RedisManager()
        return _redis_manager
    
    redis_manager = get_redis_manager()
    
    # 设置正确的Redis URL
    redis_manager.redis_url = settings.REDIS_URL
    redis_manager.password = settings.REDIS_PASSWORD

except (ImportError, AttributeError):
    # 如果common.redis_client不可用，使用本地实现
    import redis.asyncio as redis
    from typing import Optional
    
    class RedisManager:
        """Redis connection manager"""
        
        def __init__(self):
            self._redis: Optional[redis.Redis] = None
            self.redis_url = "redis://localhost:6379/2"
            self.password = None
        
        async def connect(self):
            """Connect to Redis"""
            if self._redis is None:
                self._redis = await redis.from_url(
                    self.redis_url,
                    password=self.password,
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
    
    redis_manager = RedisManager()
