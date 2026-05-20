# RAG 智能客服 - API 统一规范文档

## 📋 目录

1. [概述](#1-概述)
2. [消费者前端 API](#2-消费者前端-api)
3. [企业管理前端 API](#3-企业管理前端-api)
4. [客服坐席 API](#4-客服坐席-api)
5. [系统管理员 API](#5-系统管理员-api)
6. [Webhook 接口](#6-webhook-接口)
7. [错误码规范](#7-错误码规范)

---

## 1. 概述

### Base URL

```
API 网关: http://localhost:8080 (开发环境), https://your-domain.com (生产环境)
坐席服务: http://localhost:8006 (坐席专用)
```

### 响应格式

所有 API 响应遵循以下结构：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "code": 200
}
```

### 认证说明

- **坐席API使用 OAuth2 密码流认证
- 登录后获取 access_token，后续请求在 Authorization Header 中携带 `Bearer {token}`

---

## 2. 消费者前端 API

### 2.1 会话管理

#### 创建会话

```http
POST /api/v1/chat/sessions
Query Parameters:
  - user_id (required): 用户ID
  - enterprise_id (required): 企业ID

响应示例:
{
  "success": true,
  "data": {
    "id": "session-uuid",
    "user_id": "user-123",
    "enterprise_id": "ent-456",
    "created_at": "2024-05-18T10:30:00Z",
    "status": "active"
  }
}
```

#### 发送消息 (流式)

```http
POST /api/v1/chat/sessions/{session_id}/messages/stream
Query Parameters:
  - content (required): 消息内容
  - user_id (required): 用户ID
  - enterprise_id (required): 企业ID

响应 (SSE 流式):
data: { "type": "start", "data": {} }
data: { "type": "content", "data": { "content": "你" } }
data: { "type": "content", "data": { "content": "好" } }
data: { "type": "end"
```

#### 转接人工

```http
POST /api/v1/chat/sessions/{session_id}/escalate
Query Parameters:
  - user_id (required): 用户ID
  - reason: 转接原因 (可选)

响应示例:
{
  "success": true,
  "message": "转接请求已发送",
  "data": {
    "session_id": "session-uuid",
    "status": "pending_agent",
    "reason": "user_request",
    "created_at": "2024-05-18T10:30:00Z"
  }
}
```

---

## 3. 企业管理前端 API

### 3.1 会话监控

#### 获取待接入会话

```http
GET /api/v1/chat/sessions/pending
Headers:
  X-Enterprise-Id: 企业ID

响应示例:
{
  "success": true,
  "data": [
    {
      "id": "session-001",
      "user_id": "user-123",
      "user_name": "张三",
      "channel": "web",
      "waiting_time": 45,
      "reason": "sensitive",
      "message_preview": "你好，我想咨询...",
      "priority": "high",
      "created_at": "2024-05-18T10:30:00Z"
    }
  ]
}
```

#### 获取进行中会话

```http
GET /api/v1/chat/sessions/active
Headers:
  X-Enterprise-Id: 企业ID

响应示例:
{
  "success": true,
  "data": [
    {
      "id": "session-101",
      "user_id": "user-123",
      "user_name": "张三",
      "channel": "web",
      "created_at": "2024-05-18T10:30:00Z",
      "duration": 180,
      "messages_count": 5,
      "message_preview": "好的，谢谢...",
      "status": "active"
    }
  ]
}
```

---

## 4. 客服坐席 API

### Base URL

客服坐席API直接连接到 `http://localhost:8006

### 4.1 认证

#### 坐席登录

```http
POST /api/v1/agent/login
Content-Type: application/x-www-form-urlencoded

Body:
  username=agent1&password=123456

响应示例:
{
  "access_token": "random-token-string",
  "token_type": "bearer",
  "agent": {
    "id": "agent-uuid",
    "name": "张三",
    "username": "agent1",
    "status": "online",
    "current_chats": 0,
    "total_chats": 0,
    "max_concurrent_chats": 5,
    "enterprise_id": "enterprise-uuid",
    "email": "zhangsan@example.com",
    "created_at": "2024-05-18T10:30:00Z"
  }
}
```

#### 坐席登出

```http
POST /api/v1/agent/logout
Headers:
  Authorization: Bearer {access_token}

响应示例:
{
  "message": "登出成功"
}
```

### 4.2 坐席信息

#### 获取坐席个人信息

```http
GET /api/v1/agent/profile
Headers:
  Authorization: Bearer {access_token}

响应示例:
{
  "id": "agent-uuid",
  "name": "张三",
  "username": "agent1",
  "status": "online",
  "current_chats": 2,
  "total_chats": 15,
  "max_concurrent_chats": 5,
  "enterprise_id": "enterprise-uuid",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "description": "资深客服坐席",
  "created_at": "2024-05-18T10:30:00Z"
}
```

#### 更新坐席状态

```http
PUT /api/v1/agent/profile/status
Headers:
  Authorization: Bearer {access_token}
  Content-Type: application/json

Body:
{
  "status": "busy"
}

响应示例:
{
  "message": "状态更新成功",
  "status": "busy"
}
```

### 4.3 仪表板

#### 获取坐席仪表板统计

```http
GET /api/v1/agent/dashboard/stats
Headers:
  Authorization: Bearer {access_token}

响应示例:
{
  "active_sessions": 2,
  "waiting_sessions": 3,
  "total_chats_today": 8,
  "avg_response_time": 120.5,
  "satisfaction_rate": 0.95,
  "online_agents": 5,
  "total_agents": 8
}
```

### 4.4 会话管理

#### 获取等待接入的会话

```http
GET /api/v1/agent/chats/waiting
Headers:
  Authorization: Bearer {access_token}
Query Parameters:
  - skip: 跳过数量，默认0
  - limit: 返回数量，默认50

响应示例:
[
  {
    "id": "agent-session-uuid",
    "agent_id": null,
    "session_id": "chat-session-uuid",
    "status": "waiting",
    "started_at": "2024-05-18T10:30:00Z",
    "ended_at": null,
    "enterprise_id": "enterprise-uuid",
    "user_name": "李四",
    "topic": "退款咨询",
    "priority": 2
  }
]
```

#### 获取坐席活跃会话

```http
GET /api/v1/agent/chats/active
Headers:
  Authorization: Bearer {access_token}
Query Parameters:
  - skip: 跳过数量，默认0
  - limit: 返回数量，默认50

响应示例:
[
  {
    "id": "agent-session-uuid",
    "agent_id": "agent-uuid",
    "session_id": "chat-session-uuid",
    "status": "active",
    "started_at": "2024-05-18T10:30:00Z",
    "enterprise_id": "enterprise-uuid",
    "user_name": "王五",
    "topic": "产品使用问题",
    "priority": 1
  }
]
```

#### 获取会话详情

```http
GET /api/v1/agent/chats/{agent_session_id}
Headers:
  Authorization: Bearer {access_token}

响应示例:
{
  "agent_session": {
    "id": "agent-session-uuid",
    "session_id": "chat-session-uuid",
    "status": "active",
    "user_name": "王五",
    "topic": "产品使用问题",
    "started_at": "2024-05-18T10:30:00Z"
  },
  "messages": [
    {
      "id": "msg-uuid",
      "content": "你好，我想咨询...",
      "sender_type": "user",
      "created_at": "2024-05-18T10:30:00Z"
    }
  ]
}
```

#### 接入会话

```http
POST /api/v1/agent/chats/{session_id}/accept
Headers:
  Authorization: Bearer {access_token}

响应示例:
{
  "message": "会话接入成功",
  "session_id": "chat-session-uuid"
}
```

#### 关闭会话

```http
POST /api/v1/agent/chats/{session_id}/close
Headers:
  Authorization: Bearer {access_token}

响应示例:
{
  "message": "会话关闭成功",
  "session_id": "chat-session-uuid"
}
```

#### 坐席发送消息

```http
POST /api/v1/agent/chats/{session_id}/messages
Headers:
  Authorization: Bearer {access_token}
  Content-Type: application/json

Body:
{
  "content": "您好，我是人工客服...",
  "message_type": "agent"
}

响应示例:
{
  "message": "消息发送成功",
  "session_id": "chat-session-uuid",
  "content": "您好，我是人工客服...",
  "sender": "agent",
  "timestamp": "2024-05-18T10:30:30Z"
}
```

### 4.5 WebSocket 实时通信

#### 坐席连接

```
WebSocket URL: ws://localhost:8006/ws/agent/{agent_id}
```

连接后可发送的消息类型：

```json
{
  "type": "ping"
}
```

服务器推送的消息类型：

```json
{
  "type": "new_waiting_session",
  "data": {
    "id": "session-uuid",
    "user_name": "新用户",
    "topic": "咨询问题",
    "priority": 1,
    "started_at": "2024-05-18T10:30:00Z"
  }
}
```

```json
{
  "type": "session_accepted",
  "data": {
    "session_id": "session-uuid",
    "agent_id": "agent-uuid",
    "agent_name": "坐席姓名"
  }
}
```

### 4.6 管理员坐席管理

#### 获取坐席列表

```http
GET /api/v1/admin/agents
Headers:
  Authorization: Bearer {admin_token}
Query Parameters:
  - enterprise_id: 企业ID（可选）
  - skip: 跳过数量，默认0
  - limit: 返回数量，默认100

响应示例:
[
  {
    "id": "agent-uuid",
    "name": "张三",
    "username": "agent1",
    "status": "online",
    "current_chats": 2,
    "total_chats": 15,
    "max_concurrent_chats": 5,
    "enterprise_id": "enterprise-uuid",
    "email": "zhangsan@example.com"
  }
]
```

#### 创建坐席管理

```http
POST /api/v1/admin/agents
Headers:
  Authorization: Bearer {admin_token}
  Content-Type: application/json

Body:
{
  "name": "客服姓名",
  "username": "agent3",
  "password": "password123",
  "enterprise_id": "enterprise-uuid",
  "email": "agent@example.com",
  "phone": "13800138000",
  "max_concurrent_chats": 5,
  "description": "新加入的客服"
}

响应示例:
{
  "id": "new-agent-uuid",
  "name": "客服姓名",
  "username": "agent3",
  "status": "offline",
  "current_chats": 0,
  "total_chats": 0,
  "max_concurrent_chats": 5,
  "enterprise_id": "enterprise-uuid",
  "email": "agent@example.com",
  "phone": "13800138000",
  "created_at": "2024-05-18T10:30:00Z"
}
```

---

## 5. 错误码规范

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权或令牌无效 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

---

## 6. Webhook 事件通知

### 会话转接通知

```json
{
  "type": "escalation_request",
  "session_id": "session-001",
  "enterprise_id": "ent-123",
  "user_id": "user-456",
  "reason": "sensitive_content",
  "timestamp": "2024-05-18T10:30:00Z"
}
```
