"""
User and Enterprise database models
包含角色字段的增强
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

from .database import Base


class Enterprise(Base):
    """Enterprise/Company model"""
    __tablename__ = "enterprises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    api_key = Column(String(255), unique=True)
    qwen_model = Column(String(50), default="qwen-turbo")
    sensitive_words = Column(ARRAY(Text), default=[])
    settings = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Enterprise(id={self.id}, name={self.name})>"


class User(Base):
    """User model with role support

    角色说明：
    - consumer: 普通消费者，只能访问自己的会话和数据
    - enterprise_admin: 企业管理员，可以管理企业内部资源
    - system_admin: 系统管理员，可以管理所有租户和系统配置
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    phone = Column(String(20))
    avatar = Column(String(500))
    role = Column(
        String(20),
        default="consumer",
        index=True,
        nullable=False,
        comment="用户角色：consumer/enterprise_admin/system_admin"
    )
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"))
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    @property
    def is_system_admin(self) -> bool:
        """检查是否为系统管理员"""
        return self.role == "system_admin"

    @property
    def is_enterprise_admin(self) -> bool:
        """检查是否为企业管理员"""
        return self.role == "enterprise_admin"

    @property
    def is_consumer(self) -> bool:
        """检查是否为消费者"""
        return self.role == "consumer"

    def has_permission(self, permission: str) -> bool:
        """
        检查用户是否拥有特定权限

        Args:
            permission: 权限标识符

        Returns:
            bool: 是否拥有该权限
        """
        from common.role_permissions import (
            RoleType,
            Permission,
            has_permission
        )

        try:
            role_type = RoleType(self.role)
            perm = Permission(permission)
            return has_permission(role_type, perm)
        except (ValueError, AttributeError):
            return False
