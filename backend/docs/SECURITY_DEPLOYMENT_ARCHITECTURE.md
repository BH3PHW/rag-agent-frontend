# RAG 企业客服系统 - 安全部署架构说明

## 📅 更新日期：2026-05-19

---

## 🔒 安全架构设计

### 核心原则

1. **最小权限原则** - 每个应用只能访问所需的最小资源
2. **职责分离** - 不同角色的用户使用不同的应用
3. **独立部署** - 管理功能完全独立于业务功能
4. **深度防御** - 多层安全防护

---

## 🏗️ 三应用独立部署架构

### 应用矩阵

| 应用 | 端口 | 用户角色 | 访问范围 | 敏感度 |
|------|------|---------|---------|--------|
| **Consumer App** | 3000 | 普通用户 | 仅限自己的数据 | ⭐ |
| **Enterprise App** | 3001 | 企业管理员 | 本企业数据 | ⭐⭐ |
| **System Admin Portal** | 3002 | 系统管理员 | 所有数据和系统配置 | ⭐⭐⭐ |

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户访问层                                │
├─────────────┬─────────────────┬─────────────────┬─────────────────┤
│  普通用户    │   企业管理员     │   系统管理员     │                 │
│  (消费者)    │   (租户)        │   (平台)        │                 │
└──────┬──────┴────────┬────────┴────────┬────────┴─────────────────┘
       │               │                │
       ▼               ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐
│ Consumer App │ │Enterprise App│ │System Admin Portal   │
│   :3000      │ │   :3001      │ │     :3002            │
│              │ │              │ │                      │
│ - 聊天界面   │ │ - 知识库管理  │ │ - 用户管理            │
│ - 会话历史   │ │ - 文档管理    │ │ - 租户管理            │
│ - 反馈提交   │ │ - 企业设置    │ │ - 服务监控            │
│              │ │ - 渠道配置    │ │ - 数据分析            │
│              │ │ - 人工客服    │ │ - 告警中心            │
└──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘
       │                │                     │
       ▼                ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                        API Gateway                                │
│                      http://localhost:8080                         │
└──────────────────────────────────────────────────────────────────┘
       │                │                     │
       ▼                ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                      后端微服务集群                                │
├────────────┬─────────────┬────────────┬────────────────────────┤
│ User Svc   │  Chat Svc   │Knowledge Svc│ Analytics/Alert Svc   │
│ (用户数据)  │ (对话数据)   │ (文档数据)   │ (系统数据)             │
└────────────┴─────────────┴────────────┴────────────────────────┘
```

---

## 🔐 System Admin Portal 安全特性

### 1. 独立的认证系统

**隔离的认证存储**
```typescript
// 普通应用使用
localStorage.setItem('token', ...)

// System Admin Portal 使用
localStorage.setItem('sap_token', ...)
```

**强制的角色验证**
```python
def verify_admin_role(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithm)
    if payload.get("role") != "system_admin":
        raise HTTPException(status_code=403)
    return payload
```

### 2. API 端点隔离

**专用管理端点**
- `/api/v1/admin/*` - 仅系统管理员可访问
- `/api/v1/enterprise/*` - 企业管理员可访问
- `/api/v1/user/*` - 普通用户可访问

**认证中间件**
```python
# 所有管理端点都需要通过此中间件
admin_endpoints = ["/api/v1/admin/"]
require_admin = AdminAuthDependency()
```

### 3. IP 白名单支持（可选）

```python
ADMIN_IP_WHITELIST = [
    "192.168.1.100",  # 管理员办公网络
    "10.0.0.50",      # VPN IP
]
```

### 4. 审计日志

**记录所有管理操作**
```python
logger.info(f"[AUDIT] Admin Action | User: {user_id} | Action: {action} | Time: {timestamp}")
```

**日志内容**
- 用户 ID
- 操作类型
- 访问的端点
- 时间戳
- IP 地址
- 操作结果

---

## 📦 部署配置

### Docker Compose 部署

```yaml
# docker-compose.system-admin.yml
version: '3.8'

services:
  # 独立的管理门户
  system-admin-portal:
    build:
      context: ./frontend/apps/system-admin-portal
      dockerfile: Dockerfile
    ports:
      - "3002:3002"
    environment:
      - VITE_API_BASE_URL=http://backend:8080
    networks:
      - rag-network
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    read_only: true

networks:
  rag-network:
    driver: bridge
```

### 环境变量配置

| 变量 | 说明 | 建议值 |
|------|------|--------|
| `VITE_API_BASE_URL` | 后端 API 地址 | 生产环境使用 HTTPS |
| `VITE_APP_TITLE` | 应用标题 | System Admin Portal |
| `ADMIN_IP_WHITELIST` | 允许的 IP 列表 | 限制为内网 IP |

### Nginx 安全配置

```nginx
# System Admin Portal 专用配置
server {
    listen 3002;
    server_name admin.example.com;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # CORS 配置
    location /api {
        # 仅允许管理门户域名
        add_header Access-Control-Allow-Origin "https://admin.example.com";
        # ...
    }
}
```

---

## 🛡️ 安全最佳实践

### 1. 访问控制

**强密码策略**
- 最少 12 位字符
- 包含大小写字母、数字、特殊字符
- 定期更换（建议 90 天）

**多因素认证 (MFA)**
- TOTP（时间同步验证码）
- 短信验证码
- 硬件密钥（YubiKey）

### 2. 网络安全

**隔离管理网络**
```bash
# 限制管理端口只能从内网访问
iptables -A INPUT -p tcp --dport 3002 -s 192.168.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 3002 -j DROP
```

**使用 VPN**
- 要求管理员通过 VPN 访问管理门户
- VPN 只授权给必要的人员

### 3. 监控和告警

**设置告警规则**
- 连续 3 次登录失败 → 锁定账户
- 非工作时间的登录 → 告警
- 管理操作频率异常 → 告警
- 失败的 API 请求 → 记录

### 4. 定期审计

**月度审计任务**
1. 审查审计日志
2. 检查用户权限
3. 更新安全策略
4. 测试备份恢复

---

## 📊 权限矩阵

| 功能 | Consumer | Enterprise Admin | System Admin |
|------|----------|------------------|--------------|
| 发起聊天 | ✅ | ✅ | ✅ |
| 管理会话 | ❌ | ✅ | ✅ |
| 上传文档 | ❌ | ✅ | ✅ |
| 知识库管理 | ❌ | ✅ | ✅ |
| 企业配置 | ❌ | ✅ | ✅ |
| **租户管理** | ❌ | ❌ | ✅ |
| **用户管理** | ❌ | ❌ | ✅ |
| **服务监控** | ❌ | ❌ | ✅ |
| **系统配置** | ❌ | ❌ | ✅ |
| **审计日志** | ❌ | ❌ | ✅ |

---

## 🚀 部署检查清单

### 部署前检查

- [ ] 所有服务已完成构建
- [ ] 配置已正确设置（无硬编码密钥）
- [ ] 备份已创建
- [ ] 监控已配置
- [ ] 文档已更新

### 部署后检查

- [ ] 应用可以正常启动
- [ ] 登录功能正常
- [ ] 所有页面可访问
- [ ] API 调用正常
- [ ] 安全头已生效
- [ ] 日志正常记录
- [ ] 监控告警正常

### 安全检查

- [ ] HTTPS 已启用
- [ ] CORS 配置正确
- [ ] Token 验证正常
- [ ] 角色检查生效
- [ ] 审计日志记录
- [ ] IP 白名单生效（如启用）

---

## 📝 相关文档

- [系统管理门户集成指南](./SYSTEM_ADMIN_PORTAL_INTEGRATION.md)
- [完整项目报告](./FINAL_PROJECT_REPORT.md)
- [联调优化报告](./INTEGRATION_OPTIMIZATION_REPORT.md)

---

**安全是系统的生命线，请务必遵循以上安全实践！**

**报告编制**：AI Assistant  
**最后更新**：2026-05-19
