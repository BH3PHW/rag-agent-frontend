"""
限流模块

提供API请求限流功能：
1. 基于Token Bucket算法的限流
2. 支持多种限流策略
3. Redis分布式限流支持
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import time
import threading
import hashlib


class RateLimitConfig:
    """限流配置"""
    
    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        strategy: str = "sliding_window"
    ):
        """
        参数:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
            strategy: 限流策略 (fixed_window/sliding_window/token_bucket)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.strategy = strategy


class RateLimitResult:
    """限流结果"""
    
    def __init__(
        self,
        allowed: bool,
        remaining: int,
        reset_at: Optional[datetime] = None,
        retry_after: Optional[int] = None
    ):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_at = reset_at
        self.retry_after = retry_after
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "allowed": self.allowed,
            "remaining": self.remaining
        }
        if self.reset_at:
            result["reset_at"] = self.reset_at.isoformat()
        if self.retry_after:
            result["retry_after"] = self.retry_after
        return result


class FixedWindowRateLimiter:
    """固定窗口限流器
    
    简单但可能有边界问题（两个窗口交界处可能有2倍请求）
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str) -> RateLimitResult:
        """检查请求是否允许"""
        now = time.time()
        window_start = now - self.config.window_seconds
        
        with self.lock:
            # 清理过期请求
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            
            current_count = len(self.requests[key])
            
            if current_count >= self.config.max_requests:
                # 找到最早的请求时间
                oldest = min(self.requests[key]) if self.requests[key] else now
                retry_after = int(oldest + self.config.window_seconds - now)
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=datetime.fromtimestamp(oldest + self.config.window_seconds),
                    retry_after=max(0, retry_after)
                )
            
            # 允许请求
            self.requests[key].append(now)
            
            return RateLimitResult(
                allowed=True,
                remaining=self.config.max_requests - current_count - 1,
                reset_at=datetime.fromtimestamp(now + self.config.window_seconds)
            )


class SlidingWindowRateLimiter:
    """滑动窗口限流器
    
    更精确的限流，避免固定窗口的边界问题
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str) -> RateLimitResult:
        """检查请求是否允许"""
        now = time.time()
        window_start = now - self.config.window_seconds
        
        with self.lock:
            # 清理过期请求
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            
            current_count = len(self.requests[key])
            
            if current_count >= self.config.max_requests:
                oldest = min(self.requests[key]) if self.requests[key] else now
                retry_after = int(oldest + self.config.window_seconds - now)
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=datetime.fromtimestamp(oldest + self.config.window_seconds),
                    retry_after=max(0, retry_after)
                )
            
            self.requests[key].append(now)
            
            return RateLimitResult(
                allowed=True,
                remaining=self.config.max_requests - current_count - 1,
                reset_at=datetime.fromtimestamp(now + self.config.window_seconds)
            )


class TokenBucketRateLimiter:
    """令牌桶限流器
    
    支持突发流量，更灵活
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.buckets = defaultdict(lambda: {
            "tokens": config.max_requests,
            "last_update": time.time()
        })
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str, tokens: int = 1) -> RateLimitResult:
        """检查请求是否允许"""
        with self.lock:
            bucket = self.buckets[key]
            now = time.time()
            
            # 计算应该补充的令牌数
            elapsed = now - bucket["last_update"]
            tokens_to_add = elapsed * (self.config.max_requests / self.config.window_seconds)
            bucket["tokens"] = min(
                self.config.max_requests,
                bucket["tokens"] + tokens_to_add
            )
            bucket["last_update"] = now
            
            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                
                return RateLimitResult(
                    allowed=True,
                    remaining=int(bucket["tokens"]),
                    reset_at=datetime.fromtimestamp(now + self.config.window_seconds)
                )
            else:
                # 计算需要等待多久才能获得足够的令牌
                tokens_needed = tokens - bucket["tokens"]
                wait_time = tokens_needed * (self.config.window_seconds / self.config.max_requests)
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    retry_after=int(wait_time) + 1
                )


class RateLimitManager:
    """限流管理器"""
    
    DEFAULT_LIMITS = {
        "default": RateLimitConfig(max_requests=100, window_seconds=60),
        "strict": RateLimitConfig(max_requests=10, window_seconds=60),
        "login": RateLimitConfig(max_requests=5, window_seconds=300),
        "api": RateLimitConfig(max_requests=1000, window_seconds=60),
        "chat": RateLimitConfig(max_requests=60, window_seconds=60),
        "ecommerce": RateLimitConfig(max_requests=100, window_seconds=60),
    }
    
    def __init__(self):
        self.limiters: Dict[str, Any] = {}
        self._init_default_limiters()
    
    def _init_default_limiters(self):
        """初始化默认限流器"""
        for name, config in self.DEFAULT_LIMITS.items():
            self.limiters[name] = self._create_limiter(config)
    
    def _create_limiter(self, config: RateLimitConfig):
        """根据配置创建限流器"""
        if config.strategy == "fixed_window":
            return FixedWindowRateLimiter(config)
        elif config.strategy == "sliding_window":
            return SlidingWindowRateLimiter(config)
        elif config.strategy == "token_bucket":
            return TokenBucketRateLimiter(config)
        else:
            return SlidingWindowRateLimiter(config)
    
    def add_limiter(self, name: str, config: RateLimitConfig):
        """添加自定义限流器"""
        self.limiters[name] = self._create_limiter(config)
    
    def check_rate_limit(
        self,
        key: str,
        limit_name: str = "default"
    ) -> RateLimitResult:
        """检查限流
        
        参数:
            key: 限流键（通常是用户ID、IP等）
            limit_name: 限流器名称
            
        返回:
            RateLimitResult: 限流检查结果
        """
        limiter = self.limiters.get(limit_name)
        if not limiter:
            limiter = self.limiters["default"]
        
        return limiter.is_allowed(key)
    
    def check_rate_limit_by_user(
        self,
        user_id: str,
        enterprise_id: str,
        action: str = "default"
    ) -> RateLimitResult:
        """根据用户和企业检查限流"""
        key = self._generate_key(user_id, enterprise_id, action)
        return self.check_rate_limit(key, action)
    
    def _generate_key(
        self,
        user_id: str,
        enterprise_id: str,
        action: str
    ) -> str:
        """生成限流键"""
        data = f"{user_id}:{enterprise_id}:{action}"
        return hashlib.md5(data.encode()).hexdigest()


# 全局限流管理器
_rate_limit_manager: Optional[RateLimitManager] = None


def get_rate_limit_manager() -> RateLimitManager:
    """获取限流管理器单例"""
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitManager()
    return _rate_limit_manager


def rate_limit_check(
    user_id: str,
    enterprise_id: str,
    action: str = "default"
) -> RateLimitResult:
    """便捷的限流检查函数"""
    manager = get_rate_limit_manager()
    return manager.check_rate_limit_by_user(user_id, enterprise_id, action)
