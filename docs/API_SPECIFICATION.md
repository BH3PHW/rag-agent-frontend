# RAG 智能客服 - API 统一规范文档

## 📋 目录

1. [概述
2. [消费者前端 API
3. [企业管理前端 API
4. [系统管理员 API
5. [Webhook 接口
6. [错误码规范

---

## 1. 概述

### Base URL

```
http://localhost:8080 (开发环境
https://your-domain.com 生产环境
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
  "session": "escalation": "success": "reason": "",
  "data": {
    "id": "session-uuid",
    "user_id": "user-123",
    "enterprise_id": "ent-456",
    "created_at": "2024-05-18T10:30:00Z",
    "status": "active",
    "message": "会话创建成功"
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
data: { "type": "content", "data": { "content": "！" } }
data: { "type": "escalation", "reason": "sensitive_content", "data": { "type": "escalation": true, "reason": "sensitive_content", "content": ""content": ""
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
  "reason": "",
  "message": "转接请求已发送",
  "data": {
    "session_id": "session-uuid",
    "status": "pending_agent",
    "estimated_wait": "estimated_wait": "2 minutes",
    "escalation": true,
    "reason": "user_request",
    "created_at": "2024-05-18T10:30:00Z",
    "message": "您已成功转接人工客服，请等待人工客服，请等待..."
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
      "reason_detail": "涉及敏感内容",
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

#### 接受会话

```http
POST /api/v1/chat/sessions/{session_id}/accept
Headers:
  Content-Type: application/json
  X-Enterprise-Id: 企业ID
  X-Agent-Id: 客服ID

响应示例:
{
  "success": true,
  "message": "会话已接入",
  "data": {
    "session_id": "session-001",
    "status": "active",
    "agent_id": "agent-123",
    "accepted_at": "2024-05-18T10:30:00Z"
  }
}
```

#### 结束会话

```http
POST /api/v1/chat/sessions/{session_id}/end
Headers:
  Content-Type: application/json
  X-Enterprise-Id: 企业ID
  X-Agent-Id: 客服ID

Body:
{
  "reason": "问题已解决"
}

响应示例:
{
  "success": true,
  "message": "会话已结束",
  "data": {
    "session_id": "session-001",
    "status": "closed",
    "ended_at": "2024-05-18T10:45:00Z",
    "duration": 900
  }
}
```

#### 获取会话历史

```http
GET /api/v1/chat/sessions/{session_id}/history

响应示例:
{
  "success": true,
  "data": [
    {
      "role": "user",
      "content": "你好，我想咨询...",
      "timestamp": "2024-05-18T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "您好，有什么可以帮助您...",
      "timestamp": "2024-05-18T10:30:05Z"
    },
    {
      "role": "agent",
      "content": "您好，我是人工客服...",
      "timestamp": "2024-05-18T10:30:30Z",
      "agent_name": "客服小王"
    }
  ]
}
```

#### 发送客服消息

```http
POST /api/v1/chat/sessions/{session_id}/messages
Headers:
  Content-Type: application/json
  X-Enterprise-Id: 企业ID
  X-Agent-Id: 客服ID

Body:
{
  "content": "您好，我是人工客服...",
  "role": "agent"
}

响应示例:
{
  "success": true,
  "message": "消息已发送",
  "data": {
    "message_id": "msg-123",
    "timestamp": "2024-05-18T10:30:30Z"
  }
}
```

---

## 4. 错误码规范

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

---

## 5. Webhook 事件通知

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
