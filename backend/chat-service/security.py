"""
安全验证模块

核心功能：
1. 身份验证 - 验证用户身份的真实性
2. 权限控制 - 验证用户访问权限
3. 消费者身份核实 - 验证用户是否是真实的商城消费者
4. 电商平台身份验证 - 验证用户对订单和数据的访问权限
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
import hashlib
import hmac
import base64
import secrets


class SecurityContext:
    """安全上下文
    
    存储已验证的身份信息，在整个请求处理过程中传递
    """
    def __init__(
        self,
        is_authenticated: bool = False,
        user_id: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        verified_platform: Optional[str] = None,
        verified_platform_user_id: Optional[str] = None,
        verified_phone: Optional[str] = None,
        unified_user_id: Optional[str] = None,
        permissions: Optional[list] = None
    ):
        self.is_authenticated = is_authenticated
        self.user_id = user_id
        self.enterprise_id = enterprise_id
        self.verified_platform = verified_platform
        self.verified_platform_user_id = verified_platform_user_id
        self.verified_phone = verified_phone
        self.unified_user_id = unified_user_id
        self.permissions = permissions or []


class SecurityService:
    """安全服务
    
    提供身份验证和权限控制功能
    """
    
    @staticmethod
    def validate_user_identity(
        user_id: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> SecurityContext:
        """验证用户身份
        
        参数:
            user_id: 用户ID
            enterprise_id: 企业ID
            token: 认证Token（可选）
            
        返回:
            SecurityContext: 安全上下文对象
        """
        # TODO: 实现真实的身份验证逻辑
        # 这里应该：
        # 1. 验证 Token
        # 2. 查询用户信息
        # 3. 验证 enterprise_id
        # 4. 检查用户与企业的关系
        
        # 简单实现（生产环境需要更严格）
        if not user_id or not enterprise_id:
            return SecurityContext(is_authenticated=False)
            
        # 验证企业ID格式（简单的UUID检查）
        if not SecurityService._is_valid_uuid(enterprise_id):
            return SecurityContext(is_authenticated=False)
        
        return SecurityContext(
            is_authenticated=True,
            user_id=user_id,
            enterprise_id=enterprise_id
        )
    
    @staticmethod
    def verify_consumer_identity(
        platform_type: str,
        platform_user_id: Optional[str] = None,
        phone: Optional[str] = None,
        order_id: Optional[str] = None,
        enterprise_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """验证消费者身份
        
        验证用户是否是对应电商平台的真实消费者，
        以及是否有权限访问特定订单
        
        参数:
            platform_type: 平台类型
            platform_user_id: 平台用户ID
            phone: 手机号（可选）
            order_id: 订单ID（可选）
            enterprise_id: 企业ID
            
        返回:
            (是否验证通过, 验证详情)
        """
        details = {
            "verified": False,
            "reason": "",
            "verified_platform": None,
            "verified_unified_user_id": None
        }
        
        # 必须有 enterprise_id
        if not enterprise_id:
            details["reason"] = "缺少企业ID"
            return False, details
        
        # 必须有用户标识信息
        if not platform_user_id and not phone:
            details["reason"] = "需要提供平台用户ID或手机号"
            return False, details
        
        # TODO: 这里应该调用 channel-service 的 OneID 系统
        # 1. 查询 OneIDMapping 表
        # 2. 验证用户是否存在
        # 3. 验证平台类型是否匹配
        # 4. 如果有 order_id，验证订单是否属于该用户
        
        # 临时实现：模拟验证
        if platform_type in ["taobao", "jd", "douyin", "pinduoduo", "xianyu", "xiaohongshu"]:
            # 模拟：假设验证通过
            details["verified"] = True
            details["reason"] = "身份验证通过（模拟）"
            details["verified_platform"] = platform_type
            details["verified_unified_user_id"] = f"unified_{enterprise_id[:8]}_{platform_user_id or phone[:6]}"
            return True, details
        
        details["reason"] = "不支持的平台类型"
        return False, details
    
    @staticmethod
    def verify_order_access(
        order_id: str,
        security_context: SecurityContext
    ) -> Tuple[bool, Dict[str, Any]]:
        """验证用户是否有权限访问特定订单
        
        参数:
            order_id: 订单ID
            security_context: 安全上下文
            
        返回:
            (是否有权限, 验证详情)
        """
        details = {
            "has_access": False,
            "reason": "",
            "order_belongs_to_user": False
        }
        
        # 首先检查用户是否已认证
        if not security_context.is_authenticated:
            details["reason"] = "用户未认证"
            return False, details
        
        # TODO: 这里应该：
        # 1. 查询订单信息
        # 2. 验证订单是否属于该用户
        # 3. 验证订单所属企业是否匹配
        # 4. 检查访问权限
        
        # 临时实现
        if security_context.verified_platform:
            details["has_access"] = True
            details["order_belongs_to_user"] = True
            details["reason"] = "订单访问权限验证通过（模拟）"
            return True, details
        
        details["reason"] = "无法验证订单访问权限"
        return False, details
    
    @staticmethod
    def generate_secure_token(data: str, secret: str) -> str:
        """生成安全Token
        
        使用 HMAC-SHA256 签名生成Token
        """
        timestamp = str(int(datetime.utcnow().timestamp()))
        message = f"{data}:{timestamp}".encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        return base64.b64encode(f"{data}:{timestamp}:{signature}".encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def verify_secure_token(token: str, secret: str, max_age_seconds: int = 3600) -> Tuple[bool, Optional[str]]:
        """验证安全Token
        
        参数:
            token: Token字符串
            secret: 密钥
            max_age_seconds: Token最大有效期（秒）
            
        返回:
            (是否有效, 数据内容)
        """
        try:
            decoded = base64.b64decode(token.encode('utf-8')).decode('utf-8')
            data, timestamp_str, signature = decoded.split(':')
            timestamp = int(timestamp_str)
            
            # 检查过期
            if int(datetime.utcnow().timestamp()) - timestamp > max_age_seconds:
                return False, None
            
            # 验证签名
            expected_message = f"{data}:{timestamp_str}".encode('utf-8')
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                expected_message,
                hashlib.sha256
            ).hexdigest()
            
            if hmac.compare_digest(expected_signature, signature):
                return True, data
            
            return False, None
        except Exception:
            return False, None
    
    @staticmethod
    def _is_valid_uuid(uuid_str: str) -> bool:
        """验证是否是有效的UUID"""
        try:
            UUID(uuid_str)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def mask_sensitive_data(data: str, show_first: int = 3, show_last: int = 4) -> str:
        """脱敏敏感数据
        
        例如：138****1234, 用户****名
        """
        if not data or len(data) <= show_first + show_last:
            return "*" * len(data)
        
        return data[:show_first] + "*" * (len(data) - show_first - show_last) + data[-show_last:]


# 全局安全服务实例
_security_service: Optional[SecurityService] = None


def get_security_service() -> SecurityService:
    """获取安全服务单例"""
    global _security_service
    if _security_service is None:
        _security_service = SecurityService()
    return _security_service
