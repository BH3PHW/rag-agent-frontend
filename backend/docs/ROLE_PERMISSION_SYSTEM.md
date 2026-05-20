# 角色权限系统文档

## 📅 日期：2024-05-19

---

## 🎯 概述

本文档描述系统的三类角色及其权限控制机制，确保不同角色的用户访问相应的资源。

---

## 👥 三类角色

### 1. 消费者（Consumer）

**角色标识：** `consumer`

**定义：** 普通终端用户，通过网站或应用使用智能客服系统

**典型用户：**
- 网站访客
- 购物平台买家
- 客服系统的终端使用者

**核心权限：**

| 权限类型 | 权限标识 | 说明 |
|---------|---------|------|
| 会话管理 | `session:create` | 创建新会话 |
| 会话读取 | `session:read:own` | 读取自己的会话 |
| 会话删除 | `session:delete:own` | 删除自己的会话 |
| 消息发送 | `message:create` | 发送消息 |
| 消息读取 | `message:read:own` | 读取自己的消息 |
| 反馈创建 | `feedback:create` | 创建反馈 |
| 反馈读取 | `feedback:read:own` | 读取自己的反馈 |

**权限数量：** 7 个

---

### 2. 企业管理员（Enterprise Admin）

**角色标识：** `enterprise_admin`

**定义：** 企业内部的客服主管或管理员，负责管理企业内部的知识库、会话监控和配置

**典型用户：**
- 客服团队主管
- 企业IT管理员
- 知识库维护人员

**核心权限：**

#### 会话管理（全部）
- `session:create` - 创建会话
- `session:read:own` - 读取自己的会话
- `session:read:enterprise` - **读取企业所有会话**
- `session:delete:own` - 删除自己的会话

#### 消息管理
- `message:create` - 发送消息
- `message:read:own` - 读取自己的消息
- `message:read:enterprise` - **读取企业所有消息**

#### 知识库管理（全部）
- `knowledge_base:create` - 创建知识库
- `knowledge_base:read` - 读取知识库
- `knowledge_base:update` - 更新知识库
- `knowledge_base:delete` - 删除知识库

#### 文档管理
- `document:create` - 上传文档
- `document:read` - 读取文档
- `document:delete` - 删除文档

#### 反馈管理
- `feedback:create` - 创建反馈
- `feedback:read:own` - 读取自己的反馈
- `feedback:read:enterprise` - **读取企业所有反馈**

#### 企业管理
- `enterprise:read` - 读取企业信息
- `enterprise:update` - 更新企业配置
- `enterprise:manage_members` - **管理企业成员**

#### 用户管理
- `user:read:enterprise` - **读取企业用户**
- `user:create` - 创建用户
- `user:update` - 更新用户

#### 告警管理
- `alert:read` - 读取告警
- `alert:acknowledge` - 确认告警
- `alert:resolve` - 解决告警

**权限数量：** 26 个

**关键特性：**
- ✅ 可以管理企业内的所有会话和消息
- ✅ 可以管理知识库和文档
- ✅ 可以管理企业成员
- ❌ 不能跨企业访问数据
- ❌ 不能管理系统级配置

---

### 3. 系统管理员（System Admin）

**角色标识：** `system_admin`

**定义：** 平台运维人员，负责管理所有租户、系统配置和监控

**典型用户：**
- 平台运维工程师
- 系统架构师
- 安全审计人员

**核心权限：**

#### 企业管理员的所有权限（26个）
- 包含 `enterprise_admin` 的全部权限

#### 会话管理（扩展）
- `session:read:all` - **读取所有企业的会话**

#### 系统管理（专有）
- `system:read_all_enterprises` - **查看所有企业**
- `system:manage_enterprises` - **管理所有企业**
- `system:view_logs` - **查看系统日志**
- `system:config` - **修改系统配置**

**权限数量：** 30 个

**关键特性：**
- ✅ 可以访问所有企业的数据
- ✅ 可以管理所有租户
- ✅ 可以修改系统级配置
- ✅ 可以查看系统日志
- ✅ 可以管理系统参数

---

## 🔐 权限系统架构

### 文件结构

```
common/
├── role_permissions.py    # 角色和权限定义
└── rbac.py               # RBAC中间件和验证
```

### 核心模块

#### 1. role_permissions.py

```python
# 角色枚举
class RoleType(str, Enum):
    CONSUMER = "consumer"           # 消费者
    ENTERPRISE_ADMIN = "enterprise_admin"  # 企业管理员
    SYSTEM_ADMIN = "system_admin"    # 系统管理员

# 权限枚举
class Permission(str, Enum):
    # 会话权限
    SESSION_CREATE = "session:create"
    SESSION_READ_OWN = "session:read:own"
    SESSION_READ_ENTERPRISE = "session:read:enterprise"
    SESSION_READ_ALL = "session:read:all"

# 角色权限映射
ROLE_PERMISSIONS = {
    RoleType.CONSUMER: {...},
    RoleType.ENTERPRISE_ADMIN: {...},
    RoleType.SYSTEM_ADMIN: {...},
}
```

#### 2. rbac.py

```python
# 角色检查器
class RoleChecker:
    async def __call__(token_data):
        # 检查用户角色是否在允许列表中

# 权限检查器
class PermissionChecker:
    async def __call__(token_data):
        # 检查用户是否拥有所需权限

# 装饰器
@require_roles(RoleType.ENTERPRISE_ADMIN)  # 要求特定角色
@require_permission(Permission.SESSION_READ_ENTERPRISE)  # 要求特定权限
```

---

## 📡 API端点

### 角色查询

| 方法 | 端点 | 功能 | 权限要求 |
|------|------|------|---------|
| GET | `/api/v1/roles/` | 获取所有角色列表 | 无 |
| GET | `/api/v1/roles/{role_name}` | 获取角色详情 | 无 |
| GET | `/api/v1/roles/{role_name}/permissions` | 获取角色权限 | 无 |
| POST | `/api/v1/roles/check-permission` | 检查权限 | 无 |

### 用户角色管理

| 方法 | 端点 | 功能 | 权限要求 |
|------|------|------|---------|
| GET | `/api/v1/roles/users/{user_id}` | 获取用户角色 | 已认证 |
| PUT | `/api/v1/roles/users/{user_id}/role` | 更新用户角色 | system_admin |

---

## 🔒 权限验证流程

### 1. Token验证

```python
# 从JWT Token中提取用户信息
token_data = await get_token_data(token)
# TokenData包含：user_id, enterprise_id, role
```

### 2. 角色验证

```python
# 装饰器方式
@app.get("/admin")
async def admin_endpoint(token_data = Depends(require_roles(RoleType.ENTERPRISE_ADMIN))):
    pass

# 函数方式
def check_user_enterprise_access(token_data, target_enterprise_id):
    if token_data.role == RoleType.SYSTEM_ADMIN.value:
        return True  # 系统管理员可以访问所有企业
    return str(token_data.enterprise_id) == str(target_enterprise_id)
```

### 3. 权限验证

```python
# 检查具体权限
has_permission(RoleType.ENTERPRISE_ADMIN, Permission.SESSION_READ_ENTERPRISE)
# 返回: True
```

---

## 🏢 企业数据隔离

### 消费者和企业管理员

```
用户A (Enterprise A)
  ├── 会话1 ✅ 可访问
  ├── 会话2 ✅ 可访问
  └── 消息1 ✅ 可访问

用户A (Enterprise A) 尝试访问 Enterprise B 的数据
  └── ❌ 无权访问
```

### 系统管理员

```
系统管理员
  ├── Enterprise A 的数据 ✅ 可访问
  ├── Enterprise B 的数据 ✅ 可访问
  └── Enterprise C 的数据 ✅ 可访问
```

---

## 📊 角色统计

```python
{
  "roles": [
    {
      "role": "consumer",
      "name": "消费者",
      "name_en": "Consumer",
      "description": "普通终端用户，使用智能客服咨询问题",
      "permissions_count": 7
    },
    {
      "role": "enterprise_admin",
      "name": "企业管理员",
      "name_en": "Enterprise Administrator",
      "description": "管理企业内部知识库、会话监控、数据分析",
      "permissions_count": 26
    },
    {
      "role": "system_admin",
      "name": "系统管理员",
      "name_en": "System Administrator",
      "description": "管理所有租户、系统配置、系统监控",
      "permissions_count": 30
    }
  ]
}
```

---

## 🛠️ 使用示例

### 1. 创建带角色的用户

```python
from user_service.role_endpoints import create_user_with_role

# 创建消费者
consumer = create_user_with_role(
    db=db,
    username="john_doe",
    email="john@example.com",
    password="password123",
    role="consumer"
)

# 创建企业管理员
admin = create_user_with_role(
    db=db,
    username="admin_jane",
    email="jane@example.com",
    password="password123",
    role="enterprise_admin",
    enterprise_id=enterprise_uuid
)
```

### 2. 升级用户角色

```python
from user_service.role_endpoints import upgrade_user_to_admin

# 升级为企业管理员
user = upgrade_user_to_admin(
    db=db,
    user_id=user_uuid,
    admin_type="enterprise"
)

# 升级为系统管理员
system_admin = upgrade_user_to_admin(
    db=db,
    user_id=user_uuid,
    admin_type="system"
)
```

### 3. API端点权限控制

```python
from common.role_permissions import RoleType, Permission
from common.rbac import require_roles, require_permission

# 要求特定角色
@app.get("/api/v1/knowledge-bases")
async def list_knowledge_bases(
    token_data = Depends(require_roles(RoleType.ENTERPRISE_ADMIN))
):
    pass

# 要求特定权限
@app.get("/api/v1/admin/sessions")
async def admin_list_sessions(
    token_data = Depends(require_permission(Permission.SESSION_READ_ENTERPRISE))
):
    pass
```

---

## ⚠️ 安全注意事项

### 1. 角色分配权限

只有以下角色可以分配角色：
- ✅ 系统管理员可以分配任何角色
- ✅ 企业管理员可以分配消费者和企业管理员
- ❌ 消费者不能分配角色

### 2. 数据访问控制

- 所有API都必须验证用户的企业归属
- 跨企业访问必须通过系统管理员权限
- 敏感操作必须记录审计日志

### 3. 密码安全

- 所有密码使用bcrypt哈希存储
- 不允许明文传输密码
- 定期建议用户更换密码

---

## 📈 扩展建议

### 未来可能添加的角色

1. **Knowledge Manager（知识管理员）**
   - 专门管理知识库，不管理会话

2. **Data Analyst（数据分析师）**
   - 专门查看分析数据，不管理知识库

3. **Support Agent（客服专员）**
   - 人工客服角色，处理转接会话

### 权限粒度扩展

- 按资源类型的读写分离
- 按操作类型（创建、更新、删除）细分
- 支持权限组（将多个权限打包）

---

## ✅ 总结

本系统实现了完整的三类角色权限控制：

| 角色 | 权限数量 | 数据范围 | 主要用途 |
|------|---------|---------|---------|
| 消费者 | 7 | 仅自己 | 使用客服系统 |
| 企业管理员 | 26 | 本企业 | 管理企业客服 |
| 系统管理员 | 30 | 所有企业 | 运维管理 |

---

**编制：** 系统架构师  
**审核：** 技术负责人  
**日期：** 2024-05-19  
**版本：** 1.0.0
