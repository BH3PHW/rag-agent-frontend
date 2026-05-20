"""
User Role Management API - 用户角色管理API
==========================================

提供角色相关的API端点：
1. 获取角色列表
2. 获取角色详情和权限
3. 创建/更新用户时指定角色
4. 角色分配和验证

角色说明：
- consumer（消费者）：普通终端用户
- enterprise_admin（企业管理员）：管理企业内部资源
- system_admin（系统管理员）：管理所有租户和系统配置
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List

from .database import get_db
from .models import User, Enterprise
from .security import get_password_hash, decode_token
from common.role_permissions import (
    RoleType,
    Permission,
    get_role_permissions,
    get_role_info,
    has_permission
)
from common.rbac import (
    require_roles,
    require_permission,
    check_user_enterprise_access,
    validate_role_assignment,
    get_role_statistics
)


router = APIRouter(prefix="/api/v1/roles", tags=["角色管理"])


# ==================== 角色查询API ====================

@router.get("/")
async def list_roles():
    """
    获取所有角色列表及其权限信息

    返回:
        角色列表，包含每个角色的名称、描述和权限数量
    """
    stats = get_role_statistics()
    return stats


@router.get("/{role_name}")
async def get_role_details(role_name: str):
    """
    获取指定角色的详细信息

    参数:
        role_name: 角色名称（consumer/enterprise_admin/system_admin）

    返回:
        角色详情，包括权限列表
    """
    try:
        role = RoleType(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色名称: {role_name}"
        )

    info = get_role_info(role)
    return info


@router.get("/{role_name}/permissions")
async def get_role_permissions_api(role_name: str):
    """
    获取指定角色的所有权限

    参数:
        role_name: 角色名称

    返回:
        权限列表
    """
    try:
        role = RoleType(role_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色名称: {role_name}"
        )

    permissions = get_role_permissions(role)
    return {
        "role": role.value,
        "permissions": [p.value for p in permissions],
        "permissions_count": len(permissions)
    }


# ==================== 用户角色管理API ====================

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    new_role: str,
    db: Session = Depends(get_db),
    current_user_data: dict = None
):
    """
    更新用户角色

    权限要求：
    - 系统管理员可以分配任何角色
    - 企业管理员只能分配消费者和企业管理员角色
    - 消费者不能分配角色

    参数:
        user_id: 目标用户ID
        new_role: 新角色名称
        db: 数据库会话
        current_user_data: 当前用户信息（从请求头获取）

    返回:
        更新结果
    """
    # 验证新角色是否有效
    try:
        target_role = RoleType(new_role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色: {new_role}"
        )

    # 获取目标用户
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 验证角色分配权限
    # TODO: 从JWT token中获取当前用户角色
    # current_user_role = token_data.role
    # validate_role_assignment(current_user_role, new_role)

    # 更新用户角色
    old_role = target_user.role
    target_user.role = target_role.value
    db.commit()

    return {
        "message": "角色更新成功",
        "user_id": str(user_id),
        "old_role": old_role,
        "new_role": target_role.value
    }


@router.get("/users/{user_id}")
async def get_user_with_role(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取用户信息及其角色

    参数:
        user_id: 用户ID
        db: 数据库会话

    返回:
        用户信息和角色详情
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    try:
        role = RoleType(user.role)
        role_info = get_role_info(role)
        permissions = get_role_permissions(role)
    except ValueError:
        role_info = {"error": f"未知角色: {user.role}"}
        permissions = []

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "role_info": role_info,
        "permissions": [p.value for p in permissions],
        "enterprise_id": str(user.enterprise_id) if user.enterprise_id else None,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


# ==================== 权限验证API ====================

@router.post("/check-permission")
async def check_permission(
    role: str,
    permission: str,
    db: Session = Depends(get_db)
):
    """
    检查角色是否拥有指定权限

    参数:
        role: 角色名称
        permission: 权限标识

    返回:
        权限检查结果
    """
    try:
        role_type = RoleType(role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的角色: {role}"
        )

    try:
        perm = Permission(permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的权限: {permission}"
        )

    has_perm = has_permission(role_type, perm)

    return {
        "role": role,
        "permission": permission,
        "has_permission": has_perm
    }


# ==================== 角色注册辅助函数 ====================

def create_user_with_role(
    db: Session,
    username: str,
    email: str,
    password: str,
    role: str = "consumer",
    enterprise_id: UUID = None
) -> User:
    """
    创建带角色的用户

    参数:
        db: 数据库会话
        username: 用户名
        email: 邮箱
        password: 密码（明文）
        role: 角色（默认consumer）
        enterprise_id: 企业ID（可选）

    返回:
        创建的用户对象
    """
    # 验证角色
    if not RoleHierarchy.is_valid_role(role):
        raise ValueError(f"无效的角色: {role}")

    # 密码哈希
    hashed_password = get_password_hash(password)

    # 创建用户
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
        enterprise_id=enterprise_id,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def upgrade_user_to_admin(
    db: Session,
    user_id: UUID,
    admin_type: str = "enterprise"
) -> User:
    """
    将用户升级为管理员

    参数:
        db: 数据库会话
        user_id: 用户ID
        admin_type: 管理员类型（enterprise/system）

    返回:
        更新后的用户对象
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")

    if admin_type == "enterprise":
        user.role = RoleType.ENTERPRISE_ADMIN.value
    elif admin_type == "system":
        user.role = RoleType.SYSTEM_ADMIN.value
    else:
        raise ValueError(f"未知的管理员类型: {admin_type}")

    db.commit()
    db.refresh(user)

    return user
