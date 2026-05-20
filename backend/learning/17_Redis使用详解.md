# 第9章：Redis 缓存与高性能应用

> 🎯 **学习目标**：掌握Redis核心使用，理解高性能架构设计
> 💡 **工程化思维**：性能优化、成本控制、可观测性
> 💡 **产品化思维**：快速响应、高可用、用户体验

---

## 17.1 为什么需要Redis？

### 17.1.1 性能问题分析

```
没有Redis的场景：
┌────────────────────────────────────────────────────────────┐
│  用户请求 → 查数据库 → LLM调用 → 返回结果                    │
│  └───────────────────────────────────────────────────────┘ │
│      响应时间：1-5秒 → 用户体验差                          │
│                                                           │
│  成本问题：                                                │
│  - 数据库压力大 → 需要扩容 → 贵                           │
│  - LLM重复调用相同问题 → 成本高                          │
└────────────────────────────────────────────────────────────┘

有Redis的场景：
┌────────────────────────────────────────────────────────────┐
│  用户请求 → 查Redis缓存 → 命中立即返回                       │
│  未命中 → 查数据库/LLM → 写入缓存 → 返回结果               │
│  └───────────────────────────────────────────────────────┘ │
│      响应时间：10-100毫秒 → 用户体验飞跃                    │
│                                                           │
│  成本优势：                                                │
│  - 减少数据库压力 → 节约成本                              │
│  - 减少LLM调用 → 大幅降低API费用                        │
└────────────────────────────────────────────────────────────┘
```

### 17.1.2 工程化价值

| 使用场景 | 性能提升 | 成本节约 | 复杂度 |
|---------|---------|---------|-------|
| 会话缓存 | 10-100x | 50-80% | 低 |
| 热点数据缓存 | 5-20x | 40-70% | 中 |
| 限流计数器 | 稳定性 | - | 低 |
| 分布式锁 | 一致性 | - | 中 |

---

## 17.2 Redis 核心数据结构与使用

### 17.2.1 项目中的Redis应用场景

```
本项目Redis用途：
┌────────────────────────────────────────────────────────────┐
│  1. Token缓存（String）：                                    │
│     - JWT Token存储                                         │
│     - 过期时间控制                                          │
│     - 快速验证                                              │
│                                                           │
│  2. 会话缓存（Hash）：                                      │
│     - 聊天会话信息                                          │
│     - 上下文管理                                            │
│                                                           │
│  3. 限流计数器（String）：                                  │
│     - API调用频率限制                                       │
│     - IP限流                                               │
│                                                           │
│  4. 热点缓存（String）：                                     │
│     - 常用FAQ答案                                           │
│     - 知识库查询结果缓存                                    │
└────────────────────────────────────────────────────────────┘
```

### 17.2.2 基础配置与连接

```python
# 文件：backend/common/redis_client.py
import redis.asyncio as redis
from typing import Optional
from functools import wraps
from pydantic import BaseSettings

# 工程化：Redis配置类
class RedisSettings(BaseSettings):
    """Redis统一配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    encoding: str = "utf-8"
    decode_responses: bool = True  # 自动解码为字符串
    max_connections: int = 10  # 连接池大小
    
    class Config:
        env_prefix = "REDIS_"

settings = RedisSettings()

# 工程化：Redis连接池
class RedisClient:
    """
    Redis客户端 - 工程化封装
    
    特点：
    - 连接池管理，避免频繁创建连接
    - 自动重连
    - 统一的错误处理
    - 支持装饰器模式缓存
    """
    
    _instance: Optional['RedisClient'] = None
    _redis: Optional[redis.Redis] = None
    
    def __new__(cls):
        """单例模式 - 工程化：保证全局一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def initialize(cls):
        """初始化Redis连接池"""
        if cls._redis is None:
            cls._redis = await redis.from_url(
                f"redis://{':' + settings.password + '@' if settings.password else ''}"
                f"{settings.host}:{settings.port}/{settings.db}",
                encoding=settings.encoding,
                decode_responses=settings.decode_responses,
                max_connections=settings.max_connections
            )
    
    @classmethod
    async def get_redis(cls) -> redis.Redis:
        """获取Redis实例"""
        if cls._redis is None:
            await cls.initialize()
        return cls._redis
    
    @classmethod
    async def close(cls):
        """关闭连接"""
        if cls._redis:
            await cls._redis.close()

# 工程化：缓存装饰器
def cached(
    key_prefix: str,
    expire: int = 3600,  # 默认1小时
    key_func=None
):
    """
    缓存装饰器
    
    工程化：
    - 通用缓存装饰
    - 支持自定义key
    - 自动处理缓存读写
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存key
            if key_func:
                cache_key = key_prefix + key_func(*args, **kwargs)
            else:
                cache_key = key_prefix + str(args) + str(kwargs)
            
            # 工程化：先查缓存
            redis_client = await RedisClient.get_redis()
            cached_value = await redis_client.get(cache_key)
            
            if cached_value:
                # 缓存命中
                import json
                return json.loads(cached_value)
            
            # 缓存未命中，执行原函数
            result = await func(*args, **kwargs)
            
            # 工程化：写入缓存
            if result:
                import json
                await redis_client.setex(
                    cache_key,
                    expire,
                    json.dumps(result, ensure_ascii=False)
                )
            
            return result
        return wrapper
    return decorator
```

### 17.2.3 Token缓存使用

```python
# 文件：backend/user-service/token_service.py
from ..common.redis_client import RedisClient

class TokenService:
    """
    Token服务 - 产品化：安全+性能双重考量
    
    设计思路：
    - Redis缓存Token → 快速验证
    - JWT自验证 → 验证签名和过期时间
    - 黑名单机制 → 支持提前失效
    """
    
    TOKEN_PREFIX = "token:"
    BLACKLIST_PREFIX = "token:blacklist:"
    
    @classmethod
    async def save_token(
        cls,
        user_id: str,
        enterprise_id: str,
        token: str,
        expire: int = 86400 * 7  # 7天过期
    ):
        """保存Token"""
        redis = await RedisClient.get_redis()
        
        # 存储Token信息
        await redis.setex(
            f"{cls.TOKEN_PREFIX}{token}",
            expire,
            json.dumps({
                "user_id": user_id,
                "enterprise_id": enterprise_id
            })
        )
    
    @classmethod
    async def is_token_valid(cls, token: str) -> bool:
        """检查Token是否有效"""
        redis = await RedisClient.get_redis()
        
        # 检查是否在黑名单
        is_blacklisted = await redis.exists(
            f"{cls.BLACKLIST_PREFIX}{token}"
        )
        if is_blacklisted:
            return False
        
        # 检查是否存在
        exists = await redis.exists(f"{cls.TOKEN_PREFIX}{token}")
        return exists == 1
    
    @classmethod
    async def invalidate_token(cls, token: str):
        """使Token失效 - 产品化：安全登出"""
        redis = await RedisClient.get_redis()
        
        # 加入黑名单
        await redis.setex(
            f"{cls.BLACKLIST_PREFIX}{token}",
            86400,  # 黑名单保留24小时
            "1"
        )
```

### 17.2.4 会话缓存使用

```python
# 文件：backend/chat-service/session_service.py
from ..common.redis_client import RedisClient
from typing import List, Dict
import json

class SessionService:
    """
    会话服务 - 工程化：缓存上下文提升性能
    
    设计思路：
    - 缓存最近对话上下文
    - 避免重复查数据库
    - 快速加载上下文给LLM
    """
    
    CONTEXT_PREFIX = "session:context:"
    
    @classmethod
    async def get_recent_messages(
        cls,
        session_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """获取最近对话"""
        redis = await RedisClient.get_redis()
        
        cache_key = f"{cls.CONTEXT_PREFIX}{session_id}"
        context_data = await redis.get(cache_key)
        
        if context_data:
            messages = json.loads(context_data)
            return messages[-limit:]  # 返回最近N条
        
        return []
    
    @classmethod
    async def add_message(
        cls,
        session_id: str,
        message: Dict
    ):
        """添加消息到上下文"""
        redis = await RedisClient.get_redis()
        cache_key = f"{cls.CONTEXT_PREFIX}{session_id}"
        
        # 获取现有上下文
        context_data = await redis.get(cache_key)
        if context_data:
            messages = json.loads(context_data)
        else:
            messages = []
        
        # 添加新消息
        messages.append(message)
        
        # 保持最多30条
        if len(messages) > 30:
            messages = messages[-30:]
        
        # 保存回Redis（1小时过期）
        await redis.setex(
            cache_key,
            3600,
            json.dumps(messages)
        )
```

---

## 17.3 限流与防刷 - 产品化安全

### 17.3.1 为什么需要限流？

```
产品化思维：
┌────────────────────────────────────────────────────────────┐
│  没有限流的风险：                                            │
│  1. 恶意刷接口 → 系统瘫痪 → 所有用户不可用                  │
│  2. LLM API被刷 → 成本爆炸 → 财务损失                      │
│  3. 正常用户被影响 → 用户流失                               │
│                                                           │
│  有限流的保障：                                            │
│  1. 系统稳定 → 保证服务可用性                             │
│  2. 成本可控 → 财务安全                                    │
│  3. 公平使用 → 保护正常用户                               │
└────────────────────────────────────────────────────────────┘
```

### 17.3.2 限流实现

```python
# 文件：backend/api-gateway/limiter.py
from ..common.redis_client import RedisClient
from fastapi import HTTPException, status
from typing import Optional

class RateLimiter:
    """
    限流服务 - 工程化：多层级限流
    
    设计思路：
    - IP级限流 → 防单个IP刷量
    - 用户级限流 → 防单个用户刷量
    - 全局限流 → 保护后端
    """
    
    @classmethod
    async def check_rate_limit(
        cls,
        ip: str,
        user_id: Optional[str] = None,
        api: str = "default",
        limit_per_minute: int = 60
    ) -> bool:
        """
        检查限流
        
        Returns:
            bool: True=通过, False=限流
        """
        redis = await RedisClient.get_redis()
        
        # 1. IP级限流
        ip_key = f"rate:ip:{ip}:{api}"
        await cls._increment_counter(redis, ip_key, limit_per_minute)
        
        # 2. 用户级限流（如果有用户ID）
        if user_id:
            user_key = f"rate:user:{user_id}:{api}"
            await cls._increment_counter(redis, user_key, limit_per_minute)
        
        return True
    
    @classmethod
    async def _increment_counter(
        cls,
        redis,
        key: str,
        limit: int
    ):
        """增加计数器"""
        # 获取当前计数
        current = await redis.get(key)
        
        if current is None:
            # 第一次，设置为1，过期时间1分钟
            await redis.setex(key, 60, 1)
        else:
            count = int(current)
            if count >= limit:
                # 超过限制
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="请求太频繁，请稍后再试"
                )
            # 增加计数
            await redis.incr(key)
```

---

## 17.4 分布式锁 - 工程化并发控制

### 17.4.1 为什么需要分布式锁？

```
场景：多人同时操作同一数据
┌────────────────────────────────────────────────────────────┐
│  问题：                                                     │
│  - 多个请求同时修改同一文档                                 │
│  - 数据覆盖，数据不一致                                     │
│  - 知识库分块冲突                                           │
│                                                           │
│  解决方案：分布式锁                                         │
│  - 同一时间只有一个请求能操作                               │
│  - 保证数据一致性                                           │
└────────────────────────────────────────────────────────────┘
```

### 17.4.2 分布式锁实现

```python
# 文件：backend/common/distributed_lock.py
from ..common.redis_client import RedisClient
import time
import uuid

class DistributedLock:
    """
    分布式锁 - 工程化：安全、可重入、带超时
    
    设计思路：
    - 基于Redis SetNX
    - 超时防死锁
    - 唯一值防误删
    """
    
    def __init__(
        self,
        lock_key: str,
        expire: int = 60,  # 60秒过期
        retry_times: int = 3,  # 重试3次
        retry_delay: float = 0.1  # 每次等待0.1秒
    ):
        self.lock_key = f"lock:{lock_key}"
        self.expire = expire
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.lock_value = str(uuid.uuid4())  # 唯一值
    
    async def acquire(self) -> bool:
        """获取锁"""
        redis = await RedisClient.get_redis()
        
        for attempt in range(self.retry_times):
            # 尝试获取锁
            acquired = await redis.set(
                self.lock_key,
                self.lock_value,
                ex=self.expire,
                nx=True  # 不存在才能设置
            )
            
            if acquired:
                return True
            
            # 等待后重试
            if attempt < self.retry_times - 1:
                time.sleep(self.retry_delay)
        
        return False
    
    async def release(self):
        """释放锁 - 工程化：只释放自己的锁"""
        redis = await RedisClient.get_redis()
        
        # 获取当前值
        current_value = await redis.get(self.lock_key)
        
        # 只有值匹配才删除
        if current_value == self.lock_value:
            await redis.delete(self.lock_key)
    
    async def __aenter__(self):
        """上下文管理器进入"""
        acquired = await self.acquire()
        if not acquired:
            raise Exception("Failed to acquire lock")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        await self.release()


# 使用示例
async def process_document_with_lock(document_id: str):
    """处理文档 - 使用分布式锁"""
    async with DistributedLock(f"doc:{document_id}"):
        # 安全操作文档...
        pass
```

---

## 17.5 Redis 监控与运维 - 工程化实践

### 17.5.1 监控指标

```
工程化：Redis需要监控的指标
┌────────────────────────────────────────────────────────────┐
│  1. 性能指标：                                              │
│     - 响应时间                                              │
│     - 命中率                                                │
│                                                           │
│  2. 容量指标：                                              │
│     - 内存使用量                                            │
│     - 连接数                                                │
│                                                           │
│  3. 错误指标：                                              │
│     - 连接失败次数                                          │
│     - 超时次数                                              │
└────────────────────────────────────────────────────────────┘
```

### 17.5.2 监控实现

```python
# 文件：backend/common/redis_monitor.py
from ..common.redis_client import RedisClient
import logging
import time

logger = logging.getLogger("redis-monitor")

class RedisMonitor:
    """Redis监控 - 工程化：可观测性"""
    
    @classmethod
    async def get_stats(cls) -> dict:
        """获取Redis统计信息"""
        redis = await RedisClient.get_redis()
        
        # 获取INFO命令返回的统计
        info = await redis.info()
        
        return {
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "hit_rate": cls._calculate_hit_rate(info)
        }
    
    @classmethod
    def _calculate_hit_rate(cls, info: dict) -> float:
        """计算缓存命中率"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        
        if hits + misses == 0:
            return 0.0
        
        return hits / (hits + misses) * 100
```

---

## 17.6 本章小结

### Redis核心应用

| 功能 | 数据结构 | 价值 |
|------|---------|------|
| Token缓存 | String | 快速验证、黑名单 |
| 会话上下文 | List/JSON | 上下文管理 |
| 限流计数器 | String | 安全、成本控制 |
| 分布式锁 | String | 并发控制 |
| 热点缓存 | String | 性能提升 |

### 工程化思维要点

1. **连接池** - 复用连接，避免频繁创建
2. **单例模式** - 全局一个实例
3. **装饰器模式** - 通用缓存逻辑
4. **监控运维** - 可观测性
5. **超时控制** - 防死锁

### 产品化思维要点

1. **性能优化** - Redis让响应更快
2. **成本控制** - 减少数据库和LLM调用
3. **安全防护** - 限流防刷
4. **高可用** - 分布式锁保证一致性

### 下一步学习

- [18_Docker部署详解.md](./18_Docker部署详解.md) - 学习项目部署
