"""
System Admin Portal Integration Documentation
============================================

新的独立部署架构说明
"""

# System Admin Portal 独立部署架构

## 架构概述

System Admin Portal 现在是完全独立的前端应用程序，具有以下安全特性：

### 1. 独立部署
- 独立的域名/端口（如 admin.example.com 或 localhost:3002）
- 独立的构建和部署流程
- 独立的 Docker 容器

### 2. 安全特性

#### 认证隔离
- 独立的认证存储（sap_token vs 通用 token）
- 只接受 system_admin 角色的 token
- 独立的 Token 验证逻辑

#### API 端点隔离
- 专用管理 API 端点（/api/v1/admin/*）
- IP 白名单支持（可选）
- 完整的审计日志

#### 前端安全
- Content Security Policy (CSP) 头
- X-Frame-Options 保护
- HTTPS 强制
- 安全的 Cookie 设置

## 部署方式

### 1. Docker 部署

```bash
# 构建镜像
docker build -f frontend/apps/system-admin-portal/Dockerfile \
  -t rag-system-admin:latest \
  frontend/apps/system-admin-portal

# 运行容器
docker run -d \
  -p 3002:3002 \
  -e VITE_API_BASE_URL=http://backend:8080 \
  --name rag-system-admin \
  rag-system-admin:latest
```

### 2. Docker Compose

```bash
# 启动完整系统
docker-compose -f docker-compose.system-admin.yml up -d
```

### 3. 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| VITE_API_BASE_URL | 后端 API 地址 | http://localhost:8080 |
| VITE_APP_TITLE | 应用标题 | System Admin Portal |
| VITE_APP_VERSION | 应用版本 | 1.0.0 |

## API 端点

### 认证端点
- POST /api/v1/auth/login - 管理员登录
- POST /api/v1/auth/logout - 管理员登出
- POST /api/v1/auth/refresh - 刷新 Token
- GET /api/v1/auth/me - 获取当前管理员信息

### 管理端点（需要 system_admin 角色）
- GET /api/v1/admin/users - 获取用户列表
- GET /api/v1/admin/enterprises - 获取租户列表
- GET /api/v1/admin/services - 获取服务状态
- GET /api/v1/admin/analytics - 获取分析数据
- GET /api/v1/admin/alerts - 获取告警列表
- PUT /api/v1/admin/config - 更新系统配置

## 安全建议

### 1. 生产环境
- 使用 HTTPS
- 配置 IP 白名单
- 启用审计日志
- 定期轮换密钥

### 2. 访问控制
- 限制可访问管理门户的 IP
- 使用 VPN 或内网访问
- 启用双因素认证（建议）

### 3. 监控
- 监控失败登录尝试
- 设置告警阈值
- 定期审查审计日志

## 文件结构

```
workspace/
├── frontend/
│   └── apps/
│       └── system-admin-portal/          # 独立的管理门户
│           ├── src/
│           │   ├── auth/                 # 独立认证系统
│           │   ├── api/                  # API 客户端
│           │   ├── pages/                # 页面组件
│           │   └── App.tsx
│           ├── Dockerfile
│           └── package.json
├── backend/
│   └── common/
│       └── admin_security.py             # 后端安全模块
└── docker-compose.system-admin.yml       # 部署配置
```

## 与其他应用的隔离

### Consumer App (端口 3000)
- 普通用户使用
- 只访问用户 API
- 无法访问管理端点

### Enterprise App (端口 3001)
- 企业管理员使用
- 访问企业级 API
- 无法访问系统管理端点

### System Admin Portal (端口 3002)
- 系统管理员专用
- 访问所有管理 API
- 完全独立的认证系统

## 测试

### 本地测试
```bash
cd frontend/apps/system-admin-portal
npm install
npm run dev
```

### 访问测试
1. 打开 http://localhost:3002
2. 使用 system_admin 账号登录
3. 验证可以访问所有管理功能
4. 尝试访问普通用户端（应该被拒绝）
