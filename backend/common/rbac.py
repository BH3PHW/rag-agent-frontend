"""
Role-Based Access Control (RBAC) - 基于角色的访问控制中间件
======================================================

提供角色验证和权限检查的依赖项和装饰器
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from functools import wraps

from common.role_permissions import (
    RoleType,
    Permission,
    has_permission,
    get_role_permissions,
    ROLE_DESCRIPTIONS
)


class RoleChecker:
    """角色检查器"""

    def __init__(self, required_roles: List[RoleType]):
        self.required_roles = required_roles

    async def __call__(self, token_data):
        """检查用户角色是否在允许列表中"""
        if not token_data or not hasattr(token_data, 'role'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供有效的认证信息"
            )

        user_role = token_data.role

        # 检查是否是系统管理员（系统管理员拥有所有权限）
        if user_role == RoleType.SYSTEM_ADMIN.value:
            return token_data

        # 检查是否在允许的角色列表中
        if user_role not in [r.value for r in self.required_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {[r.value for r in self.required_roles]}"
            )

        return token_data


class PermissionChecker:
    """权限检查器"""

    def __init__(self, required_permission: Permission):
        self.required_permission = required_permission

    async def __call__(self, token_data):
        """检查用户是否拥有所需权限"""
        if not token_data or not hasattr(token_data, 'role'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供有效的认证信息"
            )

        user_role = token_data.role

        # 系统管理员拥有所有权限
        if user_role == RoleType.SYSTEM_ADMIN.value:
            return token_data

        # 检查具体权限
        if not has_permission(RoleType(user_role), self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {self.required_permission.value}"
            )

        return token_data


def require_roles(*roles: RoleType):
    """
    角色要求依赖项

    用法:
        @app.get("/admin", dependencies=[Depends(require_roles(RoleType.ENTERPRISE_ADMIN))])
        async def admin_endpoint():
            pass
    """
    return Depends(RoleChecker(list(roles)))


def require_permission(permission: Permission):
    """
    权限要求依赖项

    用法:
        @app.get("/sessions", dependencies=[Depends(require_permission(Permission.SESSION_READ_ENTERPRISE))])
        async def get_sessions():
            pass
    """
    return Depends(PermissionChecker(permission))


def check_user_enterprise_access(
    token_data,
    target_enterprise_id: str
) -> bool:
    """
    检查用户是否有权访问指定企业的数据

    Args:
        token_data: 令牌数据（包含role和enterprise_id）
        target_enterprise_id: 目标企业ID

    Returns:
        bool: 是否有权访问

    Raises:
        HTTPException: 无权访问时抛出
    """
    if not token_data or not hasattr(token_data, 'role'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的认证信息"
        )

    user_role = token_data.role

    # 系统管理员可以访问所有企业
    if user_role == RoleType.SYSTEM_ADMIN.value:
        return True

    # 检查用户是否属于目标企业
    if not hasattr(token_data, 'enterprise_id') or not token_data.enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户未关联企业"
        )

    if str(token_data.enterprise_id) != str(target_enterprise_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该企业的数据"
        )

    return True


class EnterpriseAccessControl:
    """企业访问控制器"""

    @staticmethod
    def can_read_enterprise(token_data, target_enterprise_id: str) -> bool:
        """检查是否可以读取企业信息"""
        try:
            check_user_enterprise_access(token_data, target_enterprise_id)
            return True
        except HTTPException:
            return False

    @staticmethod
    def can_manage_enterprise_users(token_data, target_enterprise_id: str) -> bool:
        """检查是否可以管理企业用户"""
        if not token_data or not hasattr(token_data, 'role'):
            return False

        user_role = token_data.role

        # 系统管理员可以管理所有企业
        if user_role == RoleType.SYSTEM_ADMIN.value:
            return True

        # 企业管理员可以管理本企业用户
        if user_role == RoleType.ENTERPRISE_ADMIN.value:
            return EnterpriseAccessControl.can_read_enterprise(token_data, target_enterprise_id)

        return False

    @staticmethod
    def can_access_session(token_data, session_enterprise_id: str) -> bool:
        """检查是否可以访问会话"""
        if not token_data or not hasattr(token_data, 'role'):
            return False

        user_role = token_data.role

        # 系统管理员可以访问所有会话
        if user_role == RoleType.SYSTEM_ADMIN.value:
            return True

        # 企业管理员和消费者只能访问本企业的会话
        if hasattr(token_data, 'enterprise_id') and token_data.enterprise_id:
            return str(token_data.enterprise_id) == str(session_enterprise_id)

        return False


def get_role_statistics() -> dict:
    """获取所有角色的统计信息"""
    return {
        "roles": [
            {
                "role": role.value,
                "name": ROLE_DESCRIPTIONS[role]["name"],
                "name_en": ROLE_DESCRIPTIONS[role]["name_en"],
                "description": ROLE_DESCRIPTIONS[role]["description"],
                "permissions_count": ROLE_DESCRIPTIONS[role]["permissions_count"],
            }
            for role in RoleType
        ]
    }


def validate_role_assignment(
    current_user_role: str,
    target_role: str
) -> bool:
    """
    验证角色分配是否合法

    规则：
    - 系统管理员可以分配任何角色
    - 企业管理员只能分配消费者和企业管理员角色
    - 消费者不能分配任何角色

    Args:
        current_user_role: 当前用户角色
        target_role: 目标角色

    Returns:
        bool: 是否允许分配

    Raises:
        HTTPException: 不允许分配时抛出
    """
    if current_user_role == RoleType.SYSTEM_ADMIN.value:
        # 系统管理员可以分配任何角色
        return True

    if current_user_role == RoleType.ENTERPRISE_ADMIN.value:
        # 企业管理员只能分配消费者和企业管理员
        allowed_roles = [RoleType.CONSUMER.value, RoleType.ENTERPRISE_ADMIN.value]
        if target_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="企业管理员无权分配系统管理员角色"
            )
        return True

    if current_user_role == RoleType.CONSUMER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="消费者无权分配角色"
        )

    return False
