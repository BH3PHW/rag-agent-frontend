"""
Role and Permission System - 角色权限系统
==========================================

定义系统中的三类角色及其权限：
1. Consumer（消费者）：普通用户，只能访问自己的会话
2. Enterprise Admin（企业管理员）：管理企业内部资源
3. System Admin（系统管理员）：管理所有租户和系统配置

权限设计原则：
- 最小权限原则：只授予完成任务所需的最小权限
- 角色分离：不同角色有明确的职责边界
- 数据隔离：企业间数据完全隔离，只有系统管理员可跨企业访问
"""
from enum import Enum
from typing import List, Set
from functools import wraps


class RoleType(str, Enum):
    """用户角色枚举"""
    CONSUMER = "consumer"           # 消费者/终端用户
    ENTERPRISE_ADMIN = "enterprise_admin"  # 企业管理员
    SYSTEM_ADMIN = "system_admin"  # 系统管理员


class Permission(str, Enum):
    """权限枚举"""
    # 会话权限
    SESSION_CREATE = "session:create"           # 创建会话
    SESSION_READ_OWN = "session:read:own"      # 读取自己的会话
    SESSION_READ_ENTERPRISE = "session:read:enterprise"  # 读取企业所有会话
    SESSION_READ_ALL = "session:read:all"      # 读取所有会话（系统管理员）
    SESSION_DELETE_OWN = "session:delete:own"   # 删除自己的会话

    # 消息权限
    MESSAGE_CREATE = "message:create"           # 发送消息
    MESSAGE_READ_OWN = "message:read:own"       # 读取自己的消息
    MESSAGE_READ_ENTERPRISE = "message:read:enterprise"  # 读取企业所有消息

    # 知识库权限
    KNOWLEDGE_BASE_CREATE = "knowledge_base:create"    # 创建知识库
    KNOWLEDGE_BASE_READ = "knowledge_base:read"       # 读取知识库
    KNOWLEDGE_BASE_UPDATE = "knowledge_base:update"    # 更新知识库
    KNOWLEDGE_BASE_DELETE = "knowledge_base:delete"    # 删除知识库

    # 文档权限
    DOCUMENT_CREATE = "document:create"        # 上传文档
    DOCUMENT_READ = "document:read"            # 读取文档
    DOCUMENT_DELETE = "document:delete"         # 删除文档

    # 反馈权限
    FEEDBACK_CREATE = "feedback:create"         # 创建反馈
    FEEDBACK_READ_OWN = "feedback:read:own"    # 读取自己的反馈
    FEEDBACK_READ_ENTERPRISE = "feedback:read:enterprise"  # 读取企业所有反馈

    # 企业管理权限
    ENTERPRISE_READ = "enterprise:read"         # 读取企业信息
    ENTERPRISE_UPDATE = "enterprise:update"     # 更新企业配置
    ENTERPRISE_MANAGE_MEMBERS = "enterprise:manage_members"  # 管理企业成员

    # 用户管理权限
    USER_READ_ENTERPRISE = "user:read:enterprise"  # 读取企业用户
    USER_CREATE = "user:create"                # 创建用户
    USER_UPDATE = "user:update"                # 更新用户
    USER_DELETE = "user:delete"                # 删除用户

    # 告警权限
    ALERT_READ = "alert:read"                  # 读取告警
    ALERT_ACKNOWLEDGE = "alert:acknowledge"    # 确认告警
    ALERT_RESOLVE = "alert:resolve"            # 解决告警

    # 系统管理权限（仅系统管理员）
    SYSTEM_READ_ALL_ENTERPRISES = "system:read_all_enterprises"  # 查看所有企业
    SYSTEM_MANAGE_ENTERPRISES = "system:manage_enterprises"  # 管理所有企业
    SYSTEM_VIEW_LOGS = "system:view_logs"      # 查看系统日志
    SYSTEM_CONFIG = "system:config"            # 修改系统配置


ROLE_PERMISSIONS = {
    RoleType.CONSUMER: {
        Permission.SESSION_CREATE,
        Permission.SESSION_READ_OWN,
        Permission.SESSION_DELETE_OWN,
        Permission.MESSAGE_CREATE,
        Permission.MESSAGE_READ_OWN,
        Permission.FEEDBACK_CREATE,
        Permission.FEEDBACK_READ_OWN,
    },
    RoleType.ENTERPRISE_ADMIN: {
        Permission.SESSION_CREATE,
        Permission.SESSION_READ_OWN,
        Permission.SESSION_READ_ENTERPRISE,
        Permission.SESSION_DELETE_OWN,
        Permission.MESSAGE_CREATE,
        Permission.MESSAGE_READ_OWN,
        Permission.MESSAGE_READ_ENTERPRISE,
        Permission.KNOWLEDGE_BASE_CREATE,
        Permission.KNOWLEDGE_BASE_READ,
        Permission.KNOWLEDGE_BASE_UPDATE,
        Permission.KNOWLEDGE_BASE_DELETE,
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_DELETE,
        Permission.FEEDBACK_CREATE,
        Permission.FEEDBACK_READ_OWN,
        Permission.FEEDBACK_READ_ENTERPRISE,
        Permission.ENTERPRISE_READ,
        Permission.ENTERPRISE_UPDATE,
        Permission.ENTERPRISE_MANAGE_MEMBERS,
        Permission.USER_READ_ENTERPRISE,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.ALERT_READ,
        Permission.ALERT_ACKNOWLEDGE,
        Permission.ALERT_RESOLVE,
    },
    RoleType.SYSTEM_ADMIN: {
        # 企业管理员的所有权限
        *ROLE_PERMISSIONS[RoleType.ENTERPRISE_ADMIN],
        # 系统管理员专有权限
        Permission.SESSION_READ_ALL,
        Permission.SYSTEM_READ_ALL_ENTERPRISES,
        Permission.SYSTEM_MANAGE_ENTERPRISES,
        Permission.SYSTEM_VIEW_LOGS,
        Permission.SYSTEM_CONFIG,
    },
}


def has_permission(role: RoleType, permission: Permission) -> bool:
    """
    检查角色是否拥有指定权限

    Args:
        role: 用户角色
        permission: 要检查的权限

    Returns:
        bool: 是否拥有该权限
    """
    if not isinstance(role, RoleType):
        try:
            role = RoleType(role)
        except ValueError:
            return False

    return permission in ROLE_PERMISSIONS.get(role, set())


def get_role_permissions(role: RoleType) -> Set[Permission]:
    """
    获取角色拥有的所有权限

    Args:
        role: 用户角色

    Returns:
        Set[Permission]: 权限集合
    """
    if not isinstance(role, RoleType):
        try:
            role = RoleType(role)
        except ValueError:
            return set()

    return ROLE_PERMISSIONS.get(role, set())


def check_permission(required_permission: Permission):
    """
    权限检查装饰器

    用法:
        @check_permission(Permission.SESSION_READ_ENTERPRISE)
        async def get_sessions():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 实际检查逻辑应在调用处实现
            # 这里只是标记权限需求
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class RoleHierarchy:
    """角色层级关系"""

    @staticmethod
    def is_valid_role(role: str) -> bool:
        """检查是否为有效角色"""
        try:
            RoleType(role)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_system_admin(role: str) -> bool:
        """检查是否为系统管理员"""
        return role == RoleType.SYSTEM_ADMIN.value

    @staticmethod
    def is_enterprise_admin(role: str) -> bool:
        """检查是否为企业管理员"""
        return role == RoleType.ENTERPRISE_ADMIN.value

    @staticmethod
    def is_consumer(role: str) -> bool:
        """检查是否为消费者"""
        return role == RoleType.CONSUMER.value

    @staticmethod
    def can_access_enterprise(role: str, user_enterprise_id: str, target_enterprise_id: str) -> bool:
        """
        检查用户是否可以访问指定企业的数据

        Args:
            role: 用户角色
            user_enterprise_id: 用户所属企业ID
            target_enterprise_id: 目标企业ID

        Returns:
            bool: 是否可以访问
        """
        # 系统管理员可以访问所有企业
        if RoleHierarchy.is_system_admin(role):
            return True

        # 其他角色只能访问自己所在企业
        return str(user_enterprise_id) == str(target_enterprise_id)

    @staticmethod
    def get_default_role() -> RoleType:
        """获取默认角色（消费者）"""
        return RoleType.CONSUMER


ROLE_DESCRIPTIONS = {
    RoleType.CONSUMER: {
        "name": "消费者",
        "name_en": "Consumer",
        "description": "普通终端用户，使用智能客服咨询问题",
        "permissions_count": len(ROLE_PERMISSIONS[RoleType.CONSUMER]),
    },
    RoleType.ENTERPRISE_ADMIN: {
        "name": "企业管理员",
        "name_en": "Enterprise Administrator",
        "description": "管理企业内部知识库、会话监控、数据分析",
        "permissions_count": len(ROLE_PERMISSIONS[RoleType.ENTERPRISE_ADMIN]),
    },
    RoleType.SYSTEM_ADMIN: {
        "name": "系统管理员",
        "name_en": "System Administrator",
        "description": "管理所有租户、系统配置、系统监控",
        "permissions_count": len(ROLE_PERMISSIONS[RoleType.SYSTEM_ADMIN]),
    },
}


def get_role_info(role: RoleType) -> dict:
    """获取角色详细信息"""
    info = ROLE_DESCRIPTIONS.get(role, {})
    permissions = list(get_role_permissions(role))

    return {
        **info,
        "permissions": [p.value for p in permissions]
    }
