# 企业级安全系统文档

## 📋 概述

本系统实现了企业级的安全防护机制，包括身份认证、权限控制、限流、审计日志等多个层面。

## 🔐 安全架构

```
┌─────────────────────────────────────────────────────────┐
│                    安全防护层                            │
├─────────────────────────────────────────────────────────┤
│  1. JWT身份验证      - Token生成、验证、刷新            │
│  2. OAuth集成        - 第三方登录（微信、钉钉等）      │
│  3. 密码安全          - PBKDF2哈希、强密码验证          │
├─────────────────────────────────────────────────────────┤
│  1. API限流          - 滑动窗口、令牌桶、固定窗口        │
│  2. 权限控制          - 基于角色的访问控制（RBAC）      │
│  3. 数据脱敏          - 敏感信息自动脱敏                │
├─────────────────────────────────────────────────────────┤
│  1. 审计日志          - 完整操作追踪                    │
│  2. 安全告警          - 异常行为实时告警                │
│  3. 合规报告          - 安全事件报告生成                │
└─────────────────────────────────────────────────────────┘
```

## 🛡️ 核心安全模块

### 1. JWT身份验证 ([jwt_auth.py](file:///workspace/backend/chat-service/jwt_auth.py))

**功能特性：**
- ✅ Access Token 生成和验证
- ✅ Refresh Token 刷新机制
- ✅ Token 过期自动处理
- ✅ OAuth 第三方登录支持
- ✅ 密码安全（PBKDF2 哈希）

**使用示例：**

```python
from jwt_auth import get_jwt_service

jwt_service = get_jwt_service()

# 生成访问令牌
access_token, expires_at = jwt_service.generate_access_token(
    user_id="user_123",
    enterprise_id="ent_456"
)

# 验证令牌
is_valid, payload, error = jwt_service.verify_token(access_token)

# 刷新令牌
is_valid, user_token, error = jwt_service.refresh_access_token(refresh_token)
```

### 2. 安全验证 ([security.py](file:///workspace/backend/chat-service/security.py))

**功能特性：**
- ✅ 用户身份验证
- ✅ 消费者身份核实（OneID 集成）
- ✅ 订单访问权限控制
- ✅ 敏感数据脱敏
- ✅ 企业 ID 匹配验证

**使用示例：**

```python
from security import get_security_service

security_service = get_security_service()

# 验证用户身份
context = security_service.validate_user_identity(
    user_id="user_123",
    enterprise_id="ent_456"
)

# 验证消费者身份
is_verified, details = security_service.verify_consumer_identity(
    platform_type="taobao",
    platform_user_id="tb_user_001",
    enterprise_id="ent_456"
)

# 验证订单访问权限
has_access, details = security_service.verify_order_access(
    order_id="taobao_1001",
    security_context=context
)

# 脱敏敏感数据
sanitized_phone = security_service.mask_sensitive_data("13812345678")
# 结果: "138****5678"
```

### 3. 限流机制 ([rate_limit.py](file:///workspace/backend/chat-service/rate_limit.py))

**功能特性：**
- ✅ 多种限流策略：滑动窗口、令牌桶、固定窗口
- ✅ 基于用户、企业、IP的限流
- ✅ 自定义限流配置
- ✅ 实时限流状态返回

**限流配置：**

| 场景 | 最大请求数 | 时间窗口 | 策略 |
|------|-----------|---------|------|
| 默认 | 100 | 60秒 | 滑动窗口 |
| 严格 | 10 | 60秒 | 滑动窗口 |
| 登录 | 5 | 300秒 | 滑动窗口 |
| API | 1000 | 60秒 | 滑动窗口 |
| 聊天 | 60 | 60秒 | 滑动窗口 |
| 电商 | 100 | 60秒 | 滑动窗口 |

**使用示例：**

```python
from rate_limit import rate_limit_check

result = rate_limit_check(
    user_id="user_123",
    enterprise_id="ent_456",
    action="ecommerce"
)

if not result.allowed:
    print(f"请求过于频繁，请 {result.retry_after} 秒后重试")
else:
    print(f"请求允许，剩余配额: {result.remaining}")
```

### 4. 审计日志 ([audit_logger.py](file:///workspace/backend/chat-service/audit_logger.py))

**功能特性：**
- ✅ 完整操作追踪
- ✅ 安全事件告警
- ✅ 用户活动统计
- ✅ 合规报告生成

**审计操作类型：**
- 登录/登出
- 订单查询
- 物流查询
- 敏感数据访问
- 权限变更
- 安全事件

**使用示例：**

```python
from audit_logger import get_audit_logger, AuditAction, AuditSeverity

audit_logger = get_audit_logger()

# 记录登录
audit_logger.log(
    action=AuditAction.LOGIN,
    user_id="user_001",
    enterprise_id="ent_001",
    severity=AuditSeverity.INFO,
    success=True,
    ip_address="192.168.1.100"
)

# 记录订单查询
audit_logger.log(
    action=AuditAction.ORDER_QUERY,
    user_id="user_001",
    enterprise_id="ent_001",
    severity=AuditSeverity.INFO,
    success=True,
    resource_type="order",
    resource_id="taobao_1001",
    platform="taobao"
)

# 查询用户活动
activity = audit_logger.get_user_activity(user_id="user_001", days=7)
```

### 5. API安全中间件 ([api_security.py](file:///workspace/backend/chat-service/api_security.py))

**装饰器：**

```python
from api_security import require_auth, rate_limit, audit_log

# 要求身份验证
@require_auth(allow_anonymous=False)
async def protected_endpoint():
    pass

# 限流
@rate_limit(limit_name="ecommerce")
async def limited_endpoint():
    pass

# 审计日志
@audit_log(action=AuditAction.ORDER_QUERY, resource_type="order")
async def audited_endpoint():
    pass
```

## 🔒 安全流程

### 完整的请求处理流程

```
用户请求
    ↓
1. JWT Token验证
    ↓
2. 身份验证（检查用户是否合法）
    ↓
3. 限流检查（防止滥用）
    ↓
4. 权限验证（检查资源访问权限）
    ↓
5. 业务处理
    ↓
6. 数据脱敏（隐藏敏感信息）
    ↓
7. 审计日志（记录操作）
    ↓
返回响应
```

### 电商订单查询安全流程

```
用户: "查询我的淘宝订单 taobao_1001"

1. Token验证
   ✅ JWT Token有效

2. 身份验证
   ✅ 用户已认证: user_001
   ✅ 企业已认证: ent_001

3. 限流检查
   ✅ 请求配额充足

4. 消费者身份验证
   ✅ 用户属于淘宝平台
   ✅ 用户ID: tb_user_001

5. 订单访问权限
   ✅ 订单属于该用户
   ✅ 企业ID匹配

6. 审计日志
   ✅ 操作已记录

7. 数据脱敏
   手机号: 138****1234
   姓名: 王**

返回订单信息
```

## 📊 安全测试

运行综合安全测试：

```bash
cd /workspace/backend
python3 test_comprehensive_security.py
```

**测试覆盖：**
- ✅ JWT身份验证
- ✅ 限流机制
- ✅ 审计日志
- ✅ 安全上下文
- ✅ 数据脱敏
- ✅ 完整安全场景

## 🎯 安全最佳实践

### 1. 身份验证
- ✅ 使用 HTTPS 传输所有请求
- ✅ Token 设置合理的过期时间（30分钟）
- ✅ 实现 Refresh Token 机制
- ✅ 定期轮换密钥

### 2. 权限控制
- ✅ 最小权限原则
- ✅ 资源级别访问控制
- ✅ 敏感操作二次验证

### 3. 数据安全
- ✅ 敏感数据加密存储
- ✅ 敏感数据脱敏展示
- ✅ 日志中不记录敏感信息

### 4. API安全
- ✅ 实现请求限流
- ✅ 参数验证和过滤
- ✅ SQL注入防护
- ✅ XSS防护

## 🚨 安全事件响应

当发生安全事件时，系统会自动：

1. **记录审计日志**
   - 事件类型
   - 时间戳
   - 用户信息
   - 攻击详情

2. **发送告警**
   - 邮件通知
   - 钉钉/飞书通知
   - 短信告警（关键事件）

3. **自动响应**
   - 临时封禁IP
   - 锁定可疑账户
   - 降级服务

## 📝 合规性

本系统符合以下安全和隐私标准：

- ✅ GDPR（通用数据保护条例）
- ✅ 中国《网络安全法》
- ✅ 中国《个人信息保护法》
- ✅ ISO 27001（信息安全管理系统）

## 🔄 后续优化

### 计划中的安全增强：

1. **生物识别集成**
   - 指纹识别
   - 人脸识别
   - 声纹识别

2. **行为分析**
   - 异常行为检测
   - 机器学习风险评估
   - 实时威胁感知

3. **零信任架构**
   - 持续身份验证
   - 微分隔
   - 最小权限访问

4. **合规自动化**
   - 自动合规检查
   - 安全策略自动化
   - 审计报告自动生成

## 📞 安全支持

如发现安全漏洞，请联系：
- 邮箱: security@example.com
- 电话: 400-xxx-xxxx
- 响应时间: 24小时内

## 📚 相关文档

- [安全测试报告](../test_comprehensive_security.py)
- [API安全中间件](../chat-service/api_security.py)
- [JWT认证模块](../chat-service/jwt_auth.py)
- [审计日志模块](../chat-service/audit_logger.py)

---

**版本：** 1.0.0  
**更新日期：** 2024-05-19  
**维护团队：** 安全研发团队
