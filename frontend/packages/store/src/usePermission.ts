import React from 'react';
import { useAppStore } from './store';
import { hasPermission, Permission, RoleType, isSystemAdmin, isEnterpriseAdmin } from './rolePermissions';

interface RequirePermissionProps {
  permission: Permission;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface RequireRoleProps {
  roles: RoleType[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface IfPermissionProps {
  permission: Permission;
  children: React.ReactNode;
}

// 权限检查组件 - 渲染受保护的内容
export function RequirePermission({ permission, children, fallback = null }: RequirePermissionProps) {
  const { currentUser } = useAppStore();
  
  if (!currentUser) {
    return fallback;
  }
  
  if (hasPermission(currentUser.role, permission)) {
    return <>{children}</>;
  }
  
  return fallback;
}

// 角色检查组件 - 渲染受保护的内容
export function RequireRole({ roles, children, fallback = null }: RequireRoleProps) {
  const { currentUser } = useAppStore();
  
  if (!currentUser) {
    return fallback;
  }
  
  if (roles.includes(currentUser.role as RoleType)) {
    return <>{children}</>;
  }
  
  return fallback;
}

// 条件渲染组件 - 根据权限显示/隐藏
export function IfPermission({ permission, children }: IfPermissionProps) {
  const { currentUser } = useAppStore();
  
  if (!currentUser) {
    return null;
  }
  
  if (hasPermission(currentUser.role, permission)) {
    return <>{children}</>;
  }
  
  return null;
}

// 系统管理员专属组件
export function SystemAdminOnly({ children, fallback = null }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  const { currentUser } = useAppStore();
  
  if (!currentUser) {
    return fallback;
  }
  
  if (isSystemAdmin(currentUser.role)) {
    return <>{children}</>;
  }
  
  return fallback;
}

// 企业管理员及以上组件
export function EnterpriseAdminOrHigher({ children, fallback = null }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  const { currentUser } = useAppStore();
  
  if (!currentUser) {
    return fallback;
  }
  
  if (isEnterpriseAdmin(currentUser.role) || isSystemAdmin(currentUser.role)) {
    return <>{children}</>;
  }
  
  return fallback;
}

// 权限Hook
export function usePermission() {
  const { currentUser } = useAppStore();
  
  return {
    hasPermission: (permission: Permission) => 
      currentUser ? hasPermission(currentUser.role, permission) : false,
    isSystemAdmin: currentUser ? isSystemAdmin(currentUser.role) : false,
    isEnterpriseAdmin: currentUser ? isEnterpriseAdmin(currentUser.role) : false,
    isConsumer: currentUser ? currentUser.role === RoleType.CONSUMER : false,
    currentRole: currentUser?.role,
  };
}
