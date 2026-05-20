# System Admin Portal 使用指南

## 📖 简介

System Admin Portal 是一个完全独立的系统管理后台，专为 RAG 企业客服系统的系统管理员设计。

### 主要功能

- ✅ **用户管理** - 管理系统管理员账户
- ✅ **租户管理** - 管理所有企业租户
- ✅ **服务监控** - 实时监控微服务健康状态
- ✅ **数据分析** - 查看系统运行统计
- ✅ **告警中心** - 管理和处理系统告警
- ✅ **系统设置** - 配置系统参数

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend/apps/system-admin-portal
npm install
```

### 2. 配置环境

复制环境变量模板并修改：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8080
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3003

### 4. 生产环境构建

```bash
npm run build
```

构建产物在 `dist/` 目录。

---

## 🐳 Docker 部署

### 方式一：独立部署

```bash
# 构建镜像
docker build -t rag-system-admin:latest \
  -f frontend/apps/system-admin-portal/Dockerfile \
  frontend/apps/system-admin-portal

# 运行容器
docker run -d \
  -p 3002:3002 \
  -e VITE_API_BASE_URL=http://your-backend:8080 \
  --name rag-system-admin \
  rag-system-admin:latest
```

### 方式二：使用 Docker Compose

```bash
# 启动
docker-compose -f docker-compose.system-admin.yml up -d

# 查看日志
docker-compose -f docker-compose.system-admin.yml logs -f

# 停止
docker-compose -f docker-compose.system-admin.yml down
```

---

## 🔐 安全特性

### 1. 独立的认证系统

- 专用的 Token 存储（`sap_token`）
- 只接受 `system_admin` 角色
- 自动 Token 验证

### 2. 角色保护

所有管理页面都受到角色保护：

```typescript
// 只有 system_admin 可以访问
if (user.role !== 'system_admin') {
  redirect('/login');
}
```

### 3. API 端点保护

后端验证：

```python
# 验证管理员角色
payload = jwt.decode(token, SECRET_KEY, algorithm)
if payload.get("role") != "system_admin":
    raise HTTPException(status_code=403)
```

---

## 📱 页面功能

### 仪表盘

系统概览页面，显示：
- 总租户数
- 总用户数
- 总会话数
- 总消息数
- 系统健康状态
- 最近告警

### 租户管理

管理所有企业租户：
- 创建租户
- 编辑租户信息
- 暂停/恢复租户
- 查看租户统计

### 用户管理

管理系统管理员：
- 创建管理员
- 编辑管理员信息
- 删除管理员
- 查看登录历史

### 服务监控

监控微服务状态：
- 实时状态显示
- 性能指标（CPU、内存）
- 告警历史

### 数据分析

查看系统数据：
- 会话统计
- 用户活跃度
- 文档使用情况
- 趋势图表

### 告警中心

管理系统告警：
- 查看所有告警
- 按状态筛选
- 确认/解决告警
- 删除告警

### 系统设置

配置系统参数：
- API Gateway 地址
- 上传大小限制
- 会话超时设置
- 调试模式
- 维护模式

---

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `VITE_API_BASE_URL` | 后端 API 地址 | 是 |
| `VITE_APP_TITLE` | 应用标题 | 否 |
| `VITE_APP_VERSION` | 应用版本 | 否 |

### Nginx 配置

```nginx
server {
    listen 3002;
    server_name admin.example.com;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8080;
        # 安全头
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🛡️ 安全建议

### 1. 生产环境

- ✅ 使用 HTTPS
- ✅ 配置 IP 白名单
- ✅ 启用审计日志
- ✅ 定期更换密钥

### 2. 访问控制

- ✅ 使用 VPN 访问
- ✅ 限制访问 IP
- ✅ 启用双因素认证（MFA）

### 3. 监控

- ✅ 监控失败登录
- ✅ 设置告警阈值
- ✅ 定期审查日志

---

## 📁 项目结构

```
system-admin-portal/
├── src/
│   ├── auth/                 # 认证系统
│   │   ├── constants.ts       # 常量定义
│   │   ├── types.ts          # 类型定义
│   │   ├── store.ts          # 认证状态
│   │   ├── ProtectedRoute.tsx # 路由保护
│   │   └── LoginPage.tsx      # 登录页面
│   ├── api/
│   │   └── client.ts          # API 客户端
│   ├── pages/                 # 页面组件
│   │   ├── Dashboard.tsx
│   │   ├── Tenants.tsx
│   │   ├── Users.tsx
│   │   ├── Services.tsx
│   │   ├── Analytics.tsx
│   │   ├── Alerts.tsx
│   │   └── Settings.tsx
│   ├── App.tsx               # 主应用
│   ├── main.tsx              # 入口文件
│   └── index.css             # 全局样式
├── Dockerfile
├── package.json
├── vite.config.ts
└── README.md
```

---

## ❓ 常见问题

### Q: 无法登录？

1. 检查后端服务是否运行
2. 确认 `VITE_API_BASE_URL` 配置正确
3. 检查用户名密码是否正确
4. 确认账户角色是否为 `system_admin`

### Q: API 请求失败？

1. 检查网络连接
2. 确认 CORS 配置正确
3. 检查 Token 是否过期
4. 查看浏览器控制台错误信息

### Q: 如何重置密码？

联系系统管理员或通过数据库直接修改。

---

## 📞 技术支持

如有问题，请联系技术支持团队。

---

**版本**: 1.0.0  
**最后更新**: 2026-05-19
