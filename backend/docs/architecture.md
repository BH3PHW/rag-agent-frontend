# RAG 智能客服系统 - 后端架构文档

## 项目概述

基于 FastAPI + LangChain + ChromaDB + Redis 的多用户智能客服系统，支持企业知识库管理和智能问答。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                               │
│                    (认证、路由、限流)                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┬───────────────┐
          │               │               │               │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
    │  用户服务   │  │ 知识库服务  │  │  问答服务   │  │  告警服务   │
    │ (FastAPI) │  │ (FastAPI) │  │ (FastAPI) │  │ (FastAPI) │
    └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
          │               │               │               │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
    │ PostgreSQL │  │  ChromaDB │  │  Qwen API  │  │   Redis   │
    │   (用户)   │  │  (向量库)  │  │  (千问)    │  │  (缓存)   │
    └───────────┘  └───────────┘  └───────────┘  └───────────┘
```

## 核心服务模块

### 1. API Gateway Service
- **职责**: 统一入口、认证鉴权、请求路由、限流
- **端口**: 8000
- **依赖**: Redis (会话)、PostgreSQL (用户)

### 2. User Management Service
- **职责**: 用户注册/登录、企业管理、权限控制
- **端口**: 8001
- **依赖**: PostgreSQL

### 3. Knowledge Base Service
- **职责**: 文档上传、文本分块、向量存储、检索
- **端口**: 8002
- **依赖**: ChromaDB、Redis

### 4. Chat Service
- **职责**: RAG 问答、上下文管理、敏感词检测
- **端口**: 8003
- **依赖**: Redis、Qwen API

### 5. Alert Service
- **职责**: 敏感问题告警、人工客服介入
- **端口**: 8004
- **依赖**: Redis (Pub/Sub)

## 数据库设计

### PostgreSQL Schema

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user', -- admin, user, agent
    enterprise_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 企业表
CREATE TABLE enterprises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255), -- 企业级API密钥
    qwen_model VARCHAR(50) DEFAULT 'qwen-turbo',
    sensitive_words TEXT[], -- 自定义敏感词
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识库表
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enterprise_id UUID REFERENCES enterprises(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    document_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    file_type VARCHAR(20),
    chunk_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processing', -- processing, ready, error
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话历史表
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    enterprise_id UUID REFERENCES enterprises(id),
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 问答记录表
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id),
    role VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    sources JSONB, -- 引用来源
    is_sensitive BOOLEAN DEFAULT FALSE,
    requires_human BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 告警记录表
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES chat_sessions(id),
    message_id UUID REFERENCES chat_messages(id),
    alert_type VARCHAR(50),
    content TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, acknowledged, resolved
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API 设计

### 认证接口
```
POST   /api/v1/auth/register          - 用户注册
POST   /api/v1/auth/login             - 用户登录
POST   /api/v1/auth/logout            - 用户登出
GET    /api/v1/auth/me                - 获取当前用户
```

### 企业管理接口
```
POST   /api/v1/enterprises            - 创建企业
GET    /api/v1/enterprises            - 获取企业列表
GET    /api/v1/enterprises/{id}      - 获取企业详情
PUT    /api/v1/enterprises/{id}       - 更新企业
DELETE /api/v1/enterprises/{id}       - 删除企业
```

### 知识库接口
```
POST   /api/v1/knowledge-bases        - 创建知识库
GET    /api/v1/knowledge-bases        - 获取知识库列表
GET    /api/v1/knowledge-bases/{id}  - 获取知识库详情
PUT    /api/v1/knowledge-bases/{id}  - 更新知识库
DELETE /api/v1/knowledge-bases/{id}  - 删除知识库

POST   /api/v1/knowledge-bases/{id}/documents - 上传文档
GET    /api/v1/knowledge-bases/{id}/documents - 获取文档列表
DELETE /api/v1/documents/{id}         - 删除文档
```

### 问答接口
```
POST   /api/v1/chat/sessions          - 创建会话
GET    /api/v1/chat/sessions         - 获取会话列表
GET    /api/v1/chat/sessions/{id}    - 获取会话详情
DELETE /api/v1/chat/sessions/{id}    - 删除会话

POST   /api/v1/chat/sessions/{id}/messages - 发送消息
GET    /api/v1/chat/sessions/{id}/messages - 获取消息历史
```

### 告警接口
```
GET    /api/v1/alerts                 - 获取告警列表
PUT    /api/v1/alerts/{id}/acknowledge - 确认告警
PUT    /api/v1/alerts/{id}/resolve    - 解决告警
GET    /api/v1/alerts/stats           - 告警统计
```

## 敏感词检测策略

### 1. 内置敏感词库
```python
SENSITIVE_KEYWORDS = [
    "投诉", "举报", "诈骗", "欺诈", "违法", "犯罪",
    "退款", "退货", "赔偿", "律师", "法院", "警察",
    # ... 更多关键词
]
```

### 2. 触发条件
- 包含敏感关键词
- 用户明确要求转人工
- 连续多次无法回答
- 负面情绪检测

### 3. 告警流程
```
用户发送消息 
    ↓
敏感词检测 
    ↓
是否触发告警？ ──是──→ 创建告警记录 ──→ Redis Pub/Sub ──→ 推送给客服
    ↓ 否
正常回复
```

## 运行环境

### Docker Compose 配置
- PostgreSQL: 5432
- Redis: 6379
- ChromaDB: 8000 (HTTP)
- API Gateway: 8000
- 各微服务: 8001-8004

### 环境变量
```bash
# 数据库
DATABASE_URL=postgresql://user:pass@postgres:5432/rag客服
REDIS_URL=redis://redis:6379/0

# 阿里云百炼 API (Qwen)
QWEN_API_KEY=your_api_key
QWEN_API_ENDPOINT=https://dashscope.aliyuncs.com/api/v1

# ChromaDB
CHROMA_HOST=chroma
CHROMA_PORT=8000
```

## 性能优化

### 1. Redis 缓存策略
- 用户会话: TTL 24h
- 知识库向量: 预加载热点数据
- API 限流: 滑动窗口

### 2. 异步处理
- 文档上传: 异步分块入库
- 向量生成: 批量处理
- 告警推送: 非阻塞

### 3. 扩展性
- 服务无状态，支持水平扩展
- ChromaDB 支持分片
- Redis Cluster 支持

## 安全措施

### 1. 认证授权
- JWT Token
- RBAC 角色权限
- 企业级 API Key

### 2. 数据隔离
- 企业数据完全隔离
- 向量数据库按企业分区

### 3. 输入验证
- 请求参数校验
- SQL 注入防护
- XSS 防护

## 项目结构

```
rag-customer-service/
├── api-gateway/              # API 网关服务
│   ├── main.py
│   ├── auth.py
│   ├── middleware.py
│   └── Dockerfile
├── user-service/              # 用户服务
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   └── Dockerfile
├── knowledge-service/         # 知识库服务
│   ├── main.py
│   ├── embeddings.py
│   ├── chunker.py
│   └── Dockerfile
├── chat-service/             # 问答服务
│   ├── main.py
│   ├── rag.py
│   ├── sensitive.py
│   └── Dockerfile
├── alert-service/            # 告警服务
│   ├── main.py
│   ├── notifier.py
│   └── Dockerfile
├── common/                   # 公共模块
│   ├── database.py
│   ├── redis.py
│   ├── config.py
│   └── security.py
├── docker-compose.yml
├── .env.example
└── README.md
```

## 部署方式

### 1. 单体部署
```bash
docker-compose up -d
```

### 2. 分布式部署
```bash
# 分别启动各服务
docker-compose -f docker-compose.gateway.yml up -d
docker-compose -f docker-compose.user.yml up -d
docker-compose -f docker-compose.knowledge.yml up -d
docker-compose -f docker-compose.chat.yml up -d
docker-compose -f docker-compose.alert.yml up -d
```

## 监控指标

### 关键指标
- QPS (每秒请求数)
- 响应延迟 P99
- 知识库检索召回率
- 问答满意度
- 告警响应时间

### 日志
- 结构化日志 (JSON)
- 分布式追踪 (OpenTelemetry)
- 错误告警
