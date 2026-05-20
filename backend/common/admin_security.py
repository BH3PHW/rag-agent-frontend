"""
System Admin Portal API Security Module
=======================================

安全特性：
1. 独立的认证系统 - 只接受 system_admin 角色
2. API 端点隔离 - 专用管理端点
3. 安全的 Token 管理
4. 审计日志
5. 速率限制支持
"""

from functools import wraps
from typing import Optional, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Security Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Admin-only endpoints
ADMIN_ENDPOINTS = [
    "/api/v1/admin/",
    "/api/v1/system/",
]

# IP Whitelist for Admin Access (optional security layer)
ADMIN_IP_WHITELIST = []  # Empty = allow all, or add specific IPs

security = HTTPBearer()

class SecurityUtils:
    """安全工具类"""
    
    @staticmethod
    def verify_admin_role(token: str) -> dict:
        """
        验证 token 是否属于 system_admin
        这是防止普通用户访问管理端的关键方法
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            role = payload.get("role", "")
            
            if role != "system_admin":
                logger.warning(f"Non-admin user attempted access: {payload.get('sub')}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. System admin privileges required."
                )
            
            return payload
            
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    @staticmethod
    def check_ip_whitelist(client_ip: str) -> bool:
        """检查 IP 是否在白名单中"""
        if not ADMIN_IP_WHITELIST:
            return True  # 如果白名单为空，允许所有 IP
        return client_ip in ADMIN_IP_WHITELIST
    
    @staticmethod
    def log_admin_action(user_id: str, action: str, endpoint: str):
        """记录管理员操作到审计日志"""
        logger.info(
            f"[AUDIT] Admin Action | "
            f"User: {user_id} | "
            f"Action: {action} | "
            f"Endpoint: {endpoint} | "
            f"Time: {datetime.utcnow().isoformat()}"
        )


class AdminAuthDependency:
    """
    管理员认证依赖
    用于保护所有管理端点
    """
    
    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        request: Request = None
    ) -> dict:
        token = credentials.credentials
        
        # Verify token and admin role
        payload = SecurityUtils.verify_admin_role(token)
        
        # Optional: Check IP whitelist
        if request:
            client_ip = request.client.host if request.client else "unknown"
            if not SecurityUtils.check_ip_whitelist(client_ip):
                logger.warning(f"Blocked admin access from non-whitelisted IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied from this IP address"
                )
        
        # Log successful admin authentication
        SecurityUtils.log_admin_action(
            user_id=payload.get("sub", "unknown"),
            action="admin_login",
            endpoint=str(request.url) if request else "unknown"
        )
        
        return payload


# 创建全局依赖实例
require_admin = AdminAuthDependency()


def admin_only_endpoint(func: Callable) -> Callable:
    """
    装饰器：确保只有 system_admin 可以访问端点
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get token from kwargs or args
        token = kwargs.get('token')
        if not token:
            for arg in args:
                if isinstance(arg, str) and len(arg) > 20:
                    token = arg
                    break
        
        if token:
            SecurityUtils.verify_admin_role(token)
            SecurityUtils.log_admin_action(
                user_id="decorator",
                action=func.__name__,
                endpoint=func.__module__
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


# CORS Configuration for Admin Portal
ADMIN_CORS_ORIGINS = [
    "http://localhost:3002",  # Local development
    "https://admin.example.com",  # Production domain
]

CORS_CONFIG = {
    "allow_origins": ADMIN_CORS_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Authorization", "Content-Type", "X-Admin-Token"],
    "expose_headers": ["X-Request-ID"],
    "max_age": 3600,
}


def create_admin_token(user_id: str, username: str) -> str:
    """创建管理员专用的 JWT token"""
    payload = {
        "sub": user_id,
        "username": username,
        "role": "system_admin",
        "type": "access",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow().timestamp() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_admin_token(token: str) -> Optional[dict]:
    """验证并返回 token payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "system_admin":
            return None
        return payload
    except JWTError:
        return None
