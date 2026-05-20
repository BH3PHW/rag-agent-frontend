"""
API安全中间件

为所有API端点提供统一的安全保护：
1. JWT身份验证
2. 限流
3. 审计日志
4. 参数验证
"""
from typing import Optional, Callable, Any
from functools import wraps
from datetime import datetime
from uuid import UUID
from fastapi import Request, HTTPException, Header
import json

try:
    from .jwt_auth import get_jwt_service
    from .security import SecurityContext, get_security_service
    from .rate_limit import rate_limit_check
    from .audit_logger import get_audit_logger, AuditAction, AuditSeverity
except ImportError:
    from jwt_auth import get_jwt_service
    from security import SecurityContext, get_security_service
    from rate_limit import rate_limit_check
    from audit_logger import get_audit_logger, AuditAction, AuditSeverity


class APIAuthenticationError(Exception):
    """API认证错误"""
    def __init__(self, message: str, error_code: str = "AUTH_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class APIPermissionError(Exception):
    """API权限错误"""
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        self.message = message
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(self.message)


class APIRateLimitError(Exception):
    """API限流错误"""
    def __init__(self, message: str, retry_after: int):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


def require_auth(
    allow_anonymous: bool = False,
    require_enterprise: bool = True
):
    """身份验证装饰器
    
    参数:
        allow_anonymous: 是否允许匿名访问
        require_enterprise: 是否需要企业ID
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取request对象（FastAPI会自动注入）
            request: Optional[Request] = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            # 从Header获取Token
            auth_header = None
            if request:
                auth_header = request.headers.get("Authorization")
            
            jwt_service = get_jwt_service()
            security_service = get_security_service()
            audit_logger = get_audit_logger()
            
            # 检查Token
            if auth_header:
                token = jwt_service.extract_token_from_header(auth_header)
                if token:
                    is_valid, payload, error = jwt_service.verify_token(token)
                    
                    if is_valid:
                        # 构建安全上下文
                        security_context = SecurityContext(
                            is_authenticated=True,
                            user_id=payload.user_id,
                            enterprise_id=payload.enterprise_id
                        )
                        
                        # 设置到请求状态中
                        if request:
                            request.state.security_context = security_context
                        
                        # 将security_context添加到函数参数
                        kwargs['security_context'] = security_context
                    else:
                        # Token无效
                        audit_logger.log(
                            action=AuditAction.AUTH_FAILED,
                            severity=AuditSeverity.WARNING,
                            success=False,
                            metadata={"error": error, "endpoint": request.url.path if request else "unknown"}
                        )
                        
                        if not allow_anonymous:
                            raise HTTPException(
                                status_code=401,
                                detail={
                                    "error": "身份验证失败",
                                    "code": "AUTH_FAILED",
                                    "detail": error
                                }
                            )
            
            # 如果不允许匿名且没有认证
            if not allow_anonymous and not kwargs.get('security_context'):
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "需要身份验证",
                        "code": "AUTH_REQUIRED"
                    }
                )
            
            # 检查企业ID
            if require_enterprise:
                security_context = kwargs.get('security_context')
                if security_context and not security_context.enterprise_id:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "缺少企业ID",
                            "code": "ENTERPRISE_REQUIRED"
                        }
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(
    resource_type: str,
    action: str = "read"
):
    """权限检查装饰器
    
    参数:
        resource_type: 资源类型 (session/message/feedback等)
        action: 操作类型 (read/write/delete)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get('request')
            security_context: Optional[SecurityContext] = kwargs.get('security_context')
            
            # 如果没有security_context，尝试从request获取
            if not security_context and request:
                security_context = getattr(request.state, 'security_context', None)
            
            # 如果仍然没有security_context，跳过权限检查（依赖require_auth）
            if not security_context:
                return await func(*args, **kwargs)
            
            # TODO: 实现真实的权限检查逻辑
            # 这里应该：
            # 1. 查询用户的权限配置
            # 2. 检查用户是否有权访问该资源
            # 3. 记录权限检查日志
            
            audit_logger = get_audit_logger()
            
            # 获取资源ID
            resource_id = None
            if 'session_id' in kwargs:
                resource_id = str(kwargs['session_id'])
            elif 'message_id' in kwargs:
                resource_id = str(kwargs['message_id'])
            
            # 检查会话所有权
            if resource_type == 'session' and resource_id:
                # TODO: 查询数据库验证会话是否属于该用户
                pass
            
            # 检查消息所有权
            if resource_type == 'message' and resource_id:
                # TODO: 查询数据库验证消息是否属于该用户
                pass
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit(
    limit_name: str = "default",
    key_func: Optional[Callable] = None
):
    """限流装饰器
    
    参数:
        limit_name: 限流器名称
        key_func: 自定义key生成函数
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get('request')
            security_context: Optional[SecurityContext] = kwargs.get('security_context')
            
            # 生成限流key
            if key_func:
                key = key_func(kwargs)
            elif security_context:
                key = f"{security_context.user_id}:{security_context.enterprise_id}"
            elif request:
                # 使用IP作为key
                client_ip = request.client.host if request.client else "unknown"
                key = f"ip:{client_ip}"
            else:
                key = "default"
            
            # 检查限流
            result = rate_limit_check(key, limit_name)
            
            if not result.allowed:
                audit_logger = get_audit_logger()
                audit_logger.log(
                    action=AuditAction.RATE_LIMIT_EXCEEDED,
                    user_id=security_context.user_id if security_context else None,
                    enterprise_id=security_context.enterprise_id if security_context else None,
                    severity=AuditSeverity.WARNING,
                    success=False,
                    metadata={
                        "limit_name": limit_name,
                        "key": key,
                        "endpoint": request.url.path if request else "unknown"
                    }
                )
                
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "请求过于频繁，请稍后再试",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "retry_after": result.retry_after
                    },
                    headers={"Retry-After": str(result.retry_after)}
                )
            
            # 添加限流信息到响应头
            if request:
                request.state.rate_limit_result = result
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_params(**validators):
    """参数验证装饰器
    
    参数:
        validators: 参数名到验证函数的映射
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for param_name, validator_func in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    is_valid, error_msg = validator_func(value)
                    
                    if not is_valid:
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "error": f"参数'{param_name}'验证失败",
                                "code": "INVALID_PARAMETER",
                                "detail": error_msg
                            }
                        )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def audit_log(
    action: AuditAction,
    resource_type: Optional[str] = None
):
    """审计日志装饰器
    
    参数:
        action: 审计操作类型
        resource_type: 资源类型
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get('request')
            security_context: Optional[SecurityContext] = kwargs.get('security_context')
            
            audit_logger = get_audit_logger()
            
            # 获取资源ID
            resource_id = None
            if 'session_id' in kwargs:
                resource_id = str(kwargs['session_id'])
            elif 'message_id' in kwargs:
                resource_id = str(kwargs['message_id'])
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功日志
                audit_logger.log(
                    action=action,
                    user_id=security_context.user_id if security_context else None,
                    enterprise_id=security_context.enterprise_id if security_context else None,
                    severity=AuditSeverity.INFO,
                    success=True,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    endpoint=request.url.path if request else None,
                    method=request.method if request else None
                )
                
                return result
                
            except Exception as e:
                # 记录失败日志
                audit_logger.log(
                    action=action,
                    user_id=security_context.user_id if security_context else None,
                    enterprise_id=security_context.enterprise_id if security_context else None,
                    severity=AuditSeverity.ERROR,
                    success=False,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    error_message=str(e)
                )
                
                raise
        
        return wrapper
    return decorator


def add_security_headers(response):
    """添加安全响应头"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# 常用验证器
class Validators:
    """常用参数验证器"""
    
    @staticmethod
    def is_valid_uuid(value: Any) -> tuple:
        """验证UUID格式"""
        try:
            UUID(str(value))
            return True, None
        except (ValueError, TypeError):
            return False, "必须是有效的UUID格式"
    
    @staticmethod
    def is_positive_int(value: Any) -> tuple:
        """验证正整数"""
        try:
            int_val = int(value)
            if int_val > 0:
                return True, None
            return False, "必须是正整数"
        except (ValueError, TypeError):
            return False, "必须是整数"
    
    @staticmethod
    def is_valid_rating(value: Any) -> tuple:
        """验证评分"""
        if value in ["thumbs_up", "thumbs_down"]:
            return True, None
        return False, "评分必须是 'thumbs_up' 或 'thumbs_down'"
    
    @staticmethod
    def max_length(max_len: int):
        """验证最大长度"""
        def validator(value: Any) -> tuple:
            if value and len(str(value)) <= max_len:
                return True, None
            return False, f"长度不能超过{max_len}个字符"
        return validator
    
    @staticmethod
    def not_empty(value: Any) -> tuple:
        """验证非空"""
        if value and str(value).strip():
            return True, None
        return False, "不能为空"
