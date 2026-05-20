"""
审计日志模块

记录系统中所有敏感操作的审计日志：
1. 用户登录/登出
2. 订单访问
3. 敏感数据查询
4. 权限变更
5. 配置修改
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import threading


class AuditAction(Enum):
    """审计操作类型"""
    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_EXPIRED = "token_expired"
    
    # 数据访问
    ORDER_QUERY = "order_query"
    ORDER_LIST = "order_list"
    LOGISTICS_QUERY = "logistics_query"
    PRODUCT_QUERY = "product_query"
    
    # 业务操作
    HUMAN_TRANSFER = "human_transfer"
    FAQ_LOOKUP = "faq_lookup"
    KB_SEARCH = "kb_search"
    
    # 安全相关
    SECURITY_BLOCK = "security_block"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PERMISSION_DENIED = "permission_denied"
    AUTH_FAILED = "auth_failed"
    
    # 配置变更
    CONFIG_UPDATE = "config_update"
    CHANNEL_CONFIG = "channel_config"
    PLATFORM_CONFIG = "platform_config"
    
    # 系统操作
    SYSTEM_ERROR = "system_error"
    API_ERROR = "api_error"


class AuditSeverity(Enum):
    """审计严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLog:
    """审计日志条目"""
    id: str
    timestamp: datetime
    action: str
    user_id: Optional[str]
    enterprise_id: Optional[str]
    severity: str
    success: bool
    
    # 请求信息
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    # 操作详情
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    platform: Optional[str] = None
    
    # 结果信息
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # 附加数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, max_buffer_size: int = 100):
        """
        参数:
            max_buffer_size: 最大缓冲大小，超过后写入磁盘
        """
        self.max_buffer_size = max_buffer_size
        self.buffer: List[AuditLog] = []
        self.lock = threading.Lock()
        self.enabled = True
    
    def log(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True,
        **kwargs
    ) -> str:
        """记录审计日志
        
        返回:
            审计日志ID
        """
        if not self.enabled:
            return None
        
        import uuid
        log_id = str(uuid.uuid4())
        
        audit_log = AuditLog(
            id=log_id,
            timestamp=datetime.utcnow(),
            action=action.value,
            user_id=user_id,
            enterprise_id=enterprise_id,
            severity=severity.value,
            success=success,
            **kwargs
        )
        
        with self.lock:
            self.buffer.append(audit_log)
            
            # 如果缓冲区已满，刷新到磁盘
            if len(self.buffer) >= self.max_buffer_size:
                self._flush()
        
        return log_id
    
    def _flush(self):
        """刷新缓冲区到磁盘"""
        if not self.buffer:
            return
        
        # TODO: 实现真实的写入逻辑（文件、数据库、Elasticsearch等）
        # 这里先打印到控制台
        for log in self.buffer:
            print(f"[AUDIT] {log.to_json()}")
        
        self.buffer.clear()
    
    def query(
        self,
        user_id: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """查询审计日志
        
        TODO: 实现真实的查询逻辑
        """
        # 模拟返回空列表
        return []
    
    def get_user_activity(
        self,
        user_id: str,
        enterprise_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """获取用户活动统计"""
        # TODO: 实现真实的统计逻辑
        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": 0,
            "action_breakdown": {},
            "success_rate": 0.0
        }
    
    def get_security_alerts(
        self,
        enterprise_id: Optional[str] = None,
        hours: int = 24,
        min_severity: AuditSeverity = AuditSeverity.WARNING
    ) -> List[AuditLog]:
        """获取安全告警"""
        # 查询所有安全相关的操作
        security_actions = [
            AuditAction.SECURITY_BLOCK.value,
            AuditAction.RATE_LIMIT_EXCEEDED.value,
            AuditAction.PERMISSION_DENIED.value,
            AuditAction.AUTH_FAILED.value,
            AuditAction.LOGIN_FAILED.value
        ]
        
        return self.query(
            enterprise_id=enterprise_id,
            severity=min_severity.value
        )
    
    def disable(self):
        """禁用审计日志"""
        self.enabled = False
    
    def enable(self):
        """启用审计日志"""
        self.enabled = True


class SecurityAuditor:
    """安全审计员
    
    专门处理安全相关的审计
    """
    
    def __init__(self, audit_logger: AuditLogger):
        self.logger = audit_logger
    
    def audit_login(
        self,
        user_id: str,
        enterprise_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """记录登录审计"""
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        
        self.logger.log(
            action=action,
            user_id=user_id,
            enterprise_id=enterprise_id,
            severity=severity,
            success=success,
            ip_address=ip_address,
            error_message=error_message
        )
    
    def audit_data_access(
        self,
        action: AuditAction,
        user_id: str,
        enterprise_id: str,
        resource_type: str,
        resource_id: str,
        success: bool,
        platform: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """记录数据访问审计"""
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        
        self.logger.log(
            action=action,
            user_id=user_id,
            enterprise_id=enterprise_id,
            severity=severity,
            success=success,
            resource_type=resource_type,
            resource_id=resource_id,
            platform=platform,
            error_message=error_message
        )
    
    def audit_security_event(
        self,
        event_type: str,
        user_id: Optional[str],
        enterprise_id: Optional[str],
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.WARNING
    ):
        """记录安全事件"""
        self.logger.log(
            action=AuditAction.SECURITY_BLOCK,
            user_id=user_id,
            enterprise_id=enterprise_id,
            severity=severity,
            success=False,
            metadata=details
        )
    
    def audit_permission_denied(
        self,
        user_id: str,
        enterprise_id: str,
        resource_type: str,
        resource_id: str,
        reason: str
    ):
        """记录权限拒绝事件"""
        self.logger.log(
            action=AuditAction.PERMISSION_DENIED,
            user_id=user_id,
            enterprise_id=enterprise_id,
            severity=AuditSeverity.WARNING,
            success=False,
            resource_type=resource_type,
            resource_id=resource_id,
            error_message=reason
        )


# 全局审计日志器
_audit_logger: Optional[AuditLogger] = None
_security_auditor: Optional[SecurityAuditor] = None


def get_audit_logger() -> AuditLogger:
    """获取审计日志器单例"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def get_security_auditor() -> SecurityAuditor:
    """获取安全审计员单例"""
    global _security_auditor
    if _security_auditor is None:
        _security_auditor = SecurityAuditor(get_audit_logger())
    return _security_auditor
