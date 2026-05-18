# RAG智能客服系统 - API规范文档

## 📋 概述

本文档描述了RAG智能客服系统的所有API接口规范，包括前端调用、API网关路由和后端微服务实现的完整映射关系。

**版本**: 1.0.0
**最后更新**: 2026-05-18

---

## 🏗️ 架构概览

### 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  前端应用       │───▶│   API Gateway    │───▶│  后端微服务     │
│  (3个应用)      │    │  (端口: 8000)    │    │  (7个服务)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 服务端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| API Gateway | 8000 | 统一入口、路由转发 |
| User Service | 8001 | 用户、企业、认证管理 |
| Chat Service | 8002 | 智能聊天、RAG查询 |
| Knowledge Service | 8003 | 知识库、文档管理 |
| Alert Service | 8004 | 告警通知 |
| Channel Service | 8005 | 多渠道接入 |
| Analytics Service | 8006 | 数据分析 |
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存/消息队列 |
| ChromaDB | 8007 | 向量数据库 |

---

## 🔌 API基础信息

### 基础URL

所有API请求的基础URL为：
```
http://localhost:8000
```

### 认证方式

大部分API需要使用Bearer Token认证：
```http
Authorization: Bearer <access_token>
```

### 请求头

```http
Content-Type: application/json
Accept: application/json
```

### 响应格式

成功响应：
```json
{
  "data": {...}
}
```

错误响应：
```json
{
  "error": "错误描述"
}
```

---

## 👤 认证API

### 1. 用户注册

```http
POST /api/v1/auth/register
```

**请求体**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**前端调用**: ✅ 所有前端应用
**后端服务**: User Service
**API网关路由**: ✅ 已实现

---

### 2. 用户登录

```http
POST /api/v1/auth/login
```

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**前端调用**: ✅ 所有前端应用
**后端服务**: User Service
**API网关路由**: ✅ 已实现

---

### 3. 获取当前用户

```http
GET /api/v1/auth/me
```

**响应**:
```json
{
  "data": {
    "id": "string",
    "username": "string",
    "email": "string",
    "role": "admin|user|agent",
    "enterprise_id": "string",
    "is_active": true,
    "is_verified": true,
    "created_at": "2026-05-18T00:00:00.000Z"
  }
}
```

**前端调用**: ✅ 所有前端应用
**后端服务**: User Service
**API网关路由**: ✅ 已实现

---

## 🏢 企业API

### 1. 创建企业

```http
POST /api/v1/enterprises
```

**请求体**:
```json
{
  "name": "string"
}
```

**响应**:
```json
{
  "data": {
    "id": "string",
    "name": "string",
    "api_key": "string",
    "qwen_model": "string",
    "created_at": "2026-05-18T00:00:00.000Z"
  }
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: User Service
**API网关路由**: ✅ 已实现

---

### 2. 获取企业信息

```http
GET /api/v1/enterprises/{enterpriseId}
```

**响应**:
```json
{
  "data": {
    "id": "string",
    "name": "string",
    "api_key": "string",
    "qwen_model": "string",
    "created_at": "2026-05-18T00:00:00.000Z"
  }
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: User Service
**API网关路由**: ✅ 已实现

---

## 📚 知识库API

### 1. 创建知识库

```http
POST /api/v1/knowledge-bases
```

**请求体**:
```json
{
  "name": "string",
  "enterprise_id": "string",
  "description": "string"
}
```

**响应**:
```json
{
  "data": {
    "id": "string",
    "name": "string",
    "description": "string",
    "enterprise_id": "string",
    "document_count": 0,
    "chunk_count": 0,
    "is_active": true,
    "created_at": "2026-05-18T00:00:00.000Z"
  }
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: Knowledge Service
**API网关路由**: ✅ 已实现

---

### 2. 获取知识库列表

```http
GET /api/v1/knowledge-bases?enterprise_id={enterpriseId}
```

**响应**:
```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "enterprise_id": "string",
      "document_count": 5,
      "chunk_count": 100,
      "is_active": true,
      "created_at": "2026-05-18T00:00:00.000Z"
    }
  ]
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: Knowledge Service
**API网关路由**: ✅ 已实现

---

### 3. 上传文档

```http
POST /api/v1/knowledge-bases/{kbId}/documents?enterprise_id={enterpriseId}
```

**Content-Type**: `multipart/form-data`

**请求体**:
```
file: [binary file]
```

**响应**:
```json
{
  "data": {
    "document_id": "string",
    "filename": "string",
    "status": "processing"
  }
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: Knowledge Service
**API网关路由**: ✅ 已实现

---

### 4. 获取文档列表

```http
GET /api/v1/knowledge-bases/{kbId}/documents?enterprise_id={enterpriseId}
```

**响应**:
```json
{
  "data": [
    {
      "id": "string",
      "filename": "string",
      "file_size": 1024,
      "file_type": "pdf",
      "chunk_count": 25,
      "status": "ready|processing|error",
      "created_at": "2026-05-18T00:00:00.000Z"
    }
  ]
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: Knowledge Service
**API网关路由**: ✅ 已实现

---

### 5. 删除文档

```http
DELETE /api/v1/documents/{docId}?enterprise_id={enterpriseId}
```

**响应**:
```json
{
  "data": null
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: Knowledge Service
**API网关路由**: ✅ 已实现

---

## 💬 聊天API

### 1. 创建会话

```http
POST /api/v1/chat/sessions
```

**请求体**:
```json
{
  "user_id": "string",
  "enterprise_id": "string",
  "title": "string"
}
```

**响应**:
```json
{
  "data": {
    "id": "string",
    "title": "string",
    "user_id": "string",
    "enterprise_id": "string",
    "message_count": 0,
    "is_active": true,
    "created_at": "2026-05-18T00:00:00.000Z"
  }
}
```

**前端调用**: ✅ Consumer, Enterprise
**后端服务**: Chat Service
**API网关路由**: ✅ 已实现

---

### 2. 获取会话列表

```http
GET /api/v1/chat/sessions?user_id={userId}&enterprise_id={enterpriseId}
```

**响应**:
```json
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "user_id": "string",
      "enterprise_id": "string",
      "message_count": 15,
      "is_active": true,
      "created_at": "2026-05-18T00:00:00.000Z"
    }
  ]
}
```

**前端调用**: ✅ Consumer, Enterprise
**后端服务**: Chat Service
**API网关路由**: ✅ 已实现

---

### 3. 发送消息

```http
POST /api/v1/chat/sessions/{sessionId}/messages
```

**请求体**:
```json
{
  "content": "string",
  "user_id": "string"
}
```

**响应**:
```json
{
  "data": {
    "message_id": "string",
    "role": "assistant",
    "content": "string",
    "sources": [
      {
        "document_id": "string",
        "chunk_id": "string",
        "content": "string",
        "score": 0.95
      }
    ],
    "is_sensitive": false,
    "requires_human": false
  }
}
```

**前端调用**: ✅ Consumer, Enterprise
**后端服务**: Chat Service
**API网关路由**: ✅ 已实现

---

### 4. 流式发送消息 (SSE)

```http
POST /api/v1/chat/stream
```

**请求体**:
```json
{
  "message": "string",
  "enterpriseId": "string"
}
```

**响应**: SSE流式响应
```
data: 第一部分内容
data: 第二部分内容
data: [DONE]
```

**前端调用**: ✅ Consumer, Enterprise
**后端服务**: Chat Service
**API网关路由**: ⚠️ 需要实现

---

### 5. 获取消息列表

```http
GET /api/v1/chat/sessions/{sessionId}/messages?user_id={userId}
```

**响应**:
```json
{
  "data": [
    {
      "id": "string",
      "role": "user|assistant",
      "content": "string",
      "sources": [],
      "is_sensitive": false,
      "requires_human": false,
      "created_at": "2026-05-18T00:00:00.000Z"
    }
  ]
}
```

**前端调用**: ✅ Consumer, Enterprise
**后端服务**: Chat Service
**API网关路由**: ✅ 已实现

---

### 6. 删除会话

```http
DELETE /api/v1/chat/sessions/{sessionId}?user_id={userId}
```

**响应**:
```json
{
  "data": null
}
```

**前端调用**: ✅ Consumer, Enterprise
**后端服务**: Chat Service
**API网关路由**: ⚠️ 需要实现

---

## 🛡️ 敏感词设置API

### 1. 获取敏感设置

```http
GET /api/v1/sensitive-settings
```

**响应**:
```json
{
  "data": {
    "enable_keyword_detection": true,
    "enable_semantic_detection": true,
    "sensitive_words": [],
    "human_required_categories": [],
    "semantic_rules": [
      {
        "id": "string",
        "category": "string",
        "description": "string",
        "keywords": [],
        "enabled": true,
        "requires_human": false
      }
    ]
  }
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: User Service
**API网关路由**: ✅ 已实现

---

### 2. 更新敏感设置

```http
PUT /api/v1/sensitive-settings
```

**请求体**:
```json
{
  "enable_keyword_detection": true,
  "enable_semantic_detection": true,
  "sensitive_words": [],
  "human_required_categories": []
}
```

**响应**:
```json
{
  "data": {
    "enable_keyword_detection": true,
    "enable_semantic_detection": true,
    "sensitive_words": [],
    "human_required_categories": [],
    "semantic_rules": []
  }
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: User Service
**API网关路由**: ✅ 已实现

---

### 3. 创建语义规则

```http
POST /api/v1/semantic-rules
```

**请求体**:
```json
{
  "category": "string",
  "description": "string",
  "keywords": [],
  "enabled": true,
  "requires_human": false
}
```

**响应**:
```json
{
  "data": {
    "id": "string",
    "category": "string",
    "description": "string",
    "keywords": [],
    "enabled": true,
    "requires_human": false
  }
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: User Service
**API网关路由**: ✅ 已实现

---

### 4. 删除语义规则

```http
DELETE /api/v1/semantic-rules/{ruleId}
```

**响应**:
```json
{
  "data": null
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: User Service
**API网关路由**: ✅ 已实现

---

## ⚠️ 告警API

### 1. 获取告警列表

```http
GET /api/v1/alerts?enterprise_id={enterpriseId}
```

**响应**:
```json
{
  "data": [
    {
      "id": "string",
      "alert_type": "string",
      "priority": "low|medium|high|urgent",
      "status": "pending|acknowledged|resolved",
      "content": "string",
      "created_at": "2026-05-18T00:00:00.000Z"
    }
  ]
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: Alert Service
**API网关路由**: ✅ 已实现

---

### 2. 确认告警

```http
PUT /api/v1/alerts/{alertId}/acknowledge
```

**响应**:
```json
{
  "data": null
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: Alert Service
**API网关路由**: ✅ 已实现

---

### 3. 解决告警

```http
PUT /api/v1/alerts/{alertId}/resolve
```

**请求体**:
```json
{
  "resolution_notes": "string"
}
```

**响应**:
```json
{
  "data": null
}
```

**前端调用**: ✅ Enterprise, System Admin
**后端服务**: Alert Service
**API网关路由**: ✅ 已实现

---

## 📋 API覆盖情况总结

### 状态标记

| 标记 | 含义 |
|------|------|
| ✅ | 已实现 |
| ⚠️ | 需要实现 |
| ❌ | 缺失 |

### API覆盖表

| API功能 | 前端调用 | 前端应用 | 后端服务 | API网关 | 状态 |
|---------|---------|---------|---------|--------|------|
| 用户注册 | ✅ | Consumer, Enterprise | User Service | ✅ | ✅ |
| 用户登录 | ✅ | Consumer, Enterprise | User Service | ✅ | ✅ |
| 获取当前用户 | ✅ | Consumer, Enterprise, System Admin | User Service | ✅ | ✅ |
| 创建企业 | ✅ | Enterprise, System Admin | User Service | ✅ | ✅ |
| 获取企业信息 | ✅ | Enterprise, System Admin | User Service | ✅ | ✅ |
| 创建知识库 | ✅ | Enterprise, System Admin | Knowledge Service | ✅ | ✅ |
| 获取知识库列表 | ✅ | Enterprise, System Admin | Knowledge Service | ✅ | ✅ |
| 上传文档 | ✅ | Enterprise, System Admin | Knowledge Service | ✅ | ✅ |
| 获取文档列表 | ✅ | Enterprise, System Admin | Knowledge Service | ✅ | ✅ |
| 删除文档 | ✅ | Enterprise, System Admin | Knowledge Service | ✅ | ✅ |
| 创建会话 | ✅ | Consumer, Enterprise | Chat Service | ✅ | ✅ |
| 获取会话列表 | ✅ | Consumer, Enterprise | Chat Service | ✅ | ✅ |
| 发送消息 | ✅ | Consumer, Enterprise | Chat Service | ✅ | ✅ |
| 流式发送消息 | ✅ | Consumer, Enterprise | Chat Service | ⚠️ | 需要实现 |
| 获取消息列表 | ✅ | Consumer, Enterprise | Chat Service | ✅ | ✅ |
| 删除会话 | ✅ | Consumer, Enterprise | Chat Service | ⚠️ | 需要实现 |
| 获取敏感设置 | ✅ | Enterprise, System Admin | User Service | ✅ | ✅ |
| 更新敏感设置 | ✅ | Enterprise, System Admin | User Service | ✅ | ✅ |
| 创建语义规则 | ✅ | Enterprise, System Admin | User Service | ✅ | ✅ |
| 删除语义规则 | ✅ | Enterprise, System Admin | User Service | ✅ | ✅ |
| 获取告警列表 | ✅ | Enterprise, System Admin | Alert Service | ✅ | ✅ |
| 确认告警 | ✅ | Enterprise, System Admin | Alert Service | ✅ | ✅ |
| 解决告警 | ✅ | Enterprise, System Admin | Alert Service | ✅ | ✅ |

### 统计汇总

- **总API数量**: 24个
- **已完整实现**: 22个 (91.7%)
- **需要实现**: 2个 (8.3%)
- **缺失API**: 0个 (0%)

---

## 🔧 待实现API

### 1. 流式发送消息

需要在API Gateway和Chat Service中实现 `/api/v1/chat/stream` 端点。

### 2. 删除会话

需要在API Gateway和Chat Service中实现删除会话的端点。

---

## 📝 使用示例

### 完整对话流程示例

```javascript
// 1. 用户登录
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user1', password: 'password123' })
});
const { access_token } = (await loginResponse.json()).data;

// 2. 创建会话
const sessionResponse = await fetch('http://localhost:8000/api/v1/chat/sessions', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}` 
  },
  body: JSON.stringify({ 
    user_id: 'user1', 
    enterprise_id: 'ent1', 
    title: '客服咨询' 
  })
});
const session = (await sessionResponse.json()).data;

// 3. 发送消息
const messageResponse = await fetch(`http://localhost:8000/api/v1/chat/sessions/${session.id}/messages`, {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}` 
  },
  body: JSON.stringify({ 
    content: '如何使用产品？', 
    user_id: 'user1' 
  })
});
const message = (await messageResponse.json()).data;

console.log('AI回复:', message.content);
```

---

## 📚 相关文档

- [产品经理视角项目整合文档](../docs/产品经理视角-项目整合说明文档.md)
- [后端API网关代码](../backend/api-gateway/main.py)
- [前端API客户端 (Consumer)](../frontend/apps/consumer/src/api/client.ts)
- [前端API客户端 (Enterprise)](../frontend/apps/enterprise/src/api/client.ts)
- [调试脚本](../tests/api-debug.js)
