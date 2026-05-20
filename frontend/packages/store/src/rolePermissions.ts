// 角色定义
export enum RoleType {
  CONSUMER = 'consumer',
  ENTERPRISE_ADMIN = 'enterprise_admin',
  SYSTEM_ADMIN = 'system_admin',
}

// 权限定义
export enum Permission {
  SESSION_CREATE = 'session:create',
  SESSION_READ_OWN = 'session:read:own',
  SESSION_READ_ENTERPRISE = 'session:read:enterprise',
  SESSION_READ_ALL = 'session:read:all',
  SESSION_DELETE_OWN = 'session:delete:own',
  
  MESSAGE_CREATE = 'message:create',
  MESSAGE_READ_OWN = 'message:read:own',
  MESSAGE_READ_ENTERPRISE = 'message:read:enterprise',
  
  KNOWLEDGE_BASE_CREATE = 'knowledge_base:create',
  KNOWLEDGE_BASE_READ = 'knowledge_base:read',
  KNOWLEDGE_BASE_UPDATE = 'knowledge_base:update',
  KNOWLEDGE_BASE_DELETE = 'knowledge_base:delete',
  
  DOCUMENT_CREATE = 'document:create',
  DOCUMENT_READ = 'document:read',
  DOCUMENT_DELETE = 'document:delete',
  
  FEEDBACK_CREATE = 'feedback:create',
  FEEDBACK_READ_OWN = 'feedback:read:own',
  FEEDBACK_READ_ENTERPRISE = 'feedback:read:enterprise',
  
  ENTERPRISE_READ = 'enterprise:read',
  ENTERPRISE_UPDATE = 'enterprise:update',
  ENTERPRISE_MANAGE_MEMBERS = 'enterprise:manage_members',
  
  USER_READ_ENTERPRISE = 'user:read:enterprise',
  USER_CREATE = 'user:create',
  USER_UPDATE = 'user:update',
  USER_DELETE = 'user:delete',
  
  ALERT_READ = 'alert:read',
  ALERT_ACKNOWLEDGE = 'alert:acknowledge',
  ALERT_RESOLVE = 'alert:resolve',
  
  SYSTEM_READ_ALL_ENTERPRISES = 'system:read_all_enterprises',
  SYSTEM_MANAGE_ENTERPRISES = 'system:manage_enterprises',
  SYSTEM_VIEW_LOGS = 'system:view_logs',
  SYSTEM_CONFIG = 'system:config',
}

// 角色权限映射
export const ROLE_PERMISSIONS: Record<RoleType, Set<Permission>> = {
  [RoleType.CONSUMER]: new Set([
    Permission.SESSION_CREATE,
    Permission.SESSION_READ_OWN,
    Permission.SESSION_DELETE_OWN,
    Permission.MESSAGE_CREATE,
    Permission.MESSAGE_READ_OWN,
    Permission.FEEDBACK_CREATE,
    Permission.FEEDBACK_READ_OWN,
  ]),
  [RoleType.ENTERPRISE_ADMIN]: new Set([
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
  ]),
  [RoleType.SYSTEM_ADMIN]: new Set([
    Permission.SESSION_CREATE,
    Permission.SESSION_READ_OWN,
    Permission.SESSION_READ_ENTERPRISE,
    Permission.SESSION_READ_ALL,
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
    Permission.USER_DELETE,
    Permission.ALERT_READ,
    Permission.ALERT_ACKNOWLEDGE,
    Permission.ALERT_RESOLVE,
    Permission.SYSTEM_READ_ALL_ENTERPRISES,
    Permission.SYSTEM_MANAGE_ENTERPRISES,
    Permission.SYSTEM_VIEW_LOGS,
    Permission.SYSTEM_CONFIG,
  ]),
};

// 角色信息
export const ROLE_INFO: Record<RoleType, { name: string; nameEn: string; description: string }> = {
  [RoleType.CONSUMER]: {
    name: '消费者',
    nameEn: 'Consumer',
    description: '普通终端用户，使用智能客服系统',
  },
  [RoleType.ENTERPRISE_ADMIN]: {
    name: '企业管理员',
    nameEn: 'Enterprise Administrator',
    description: '管理企业内部知识库、会话监控、数据分析',
  },
  [RoleType.SYSTEM_ADMIN]: {
    name: '系统管理员',
    nameEn: 'System Administrator',
    description: '管理所有租户、系统配置、系统监控',
  },
};

// 检查角色是否有权限
export function hasPermission(role: string, permission: Permission): boolean {
  try {
    const roleType = role as RoleType;
    return ROLE_PERMISSIONS[roleType]?.has(permission) ?? false;
  } catch {
    return false;
  }
}

// 获取角色的所有权限
export function getRolePermissions(role: string): Permission[] {
  try {
    const roleType = role as RoleType;
    return Array.from(ROLE_PERMISSIONS[roleType] ?? []);
  } catch {
    return [];
  }
}

// 检查是否可以访问企业数据
export function canAccessEnterprise(
  userRole: string,
  userEnterpriseId: string,
  targetEnterpriseId: string
): boolean {
  // 系统管理员可以访问所有企业
  if (userRole === RoleType.SYSTEM_ADMIN) {
    return true;
  }
  
  // 其他角色只能访问自己的企业
  return userEnterpriseId === targetEnterpriseId;
}

// 检查角色级别
export function isSystemAdmin(role: string): boolean {
  return role === RoleType.SYSTEM_ADMIN;
}

export function isEnterpriseAdmin(role: string): boolean {
  return role === RoleType.ENTERPRISE_ADMIN;
}

export function isConsumer(role: string): boolean {
  return role === RoleType.CONSUMER;
}
