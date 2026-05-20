# RAG智能客服系统 - 后端服务

## 项目简介

RAG智能客服系统后端服务，采用微服务架构，包含8个独立服务。支持流式RAG智能问答、知识库管理、多租户隔离、防提示词注入等企业级功能。

## 技术栈

- **框架**: FastAPI
- **数据库**: PostgreSQL + SQLAlchemy ORM
- **缓存**: Redis
- **向量数据库**: ChromaDB
- **向量嵌入**: OpenAI Embedding
- **LLM集成**: OpenAI GPT-4
- **认证**: JWT + bcrypt

## 微服务架构

```
后端服务
├── api-gateway (8080)      # API网关 - 统一入口
├── user-service (8001)     # 用户服务 - 认证、企业管理
├── chat-service (8002)     # 聊天服务 - RAG问答、流式输出
├── knowledge-service (8003) # 知识库服务 - 文档管理、向量化
├── alert-service (8004)   # 告警服务 - 敏感内容告警
├── channel-service (8005) # 渠道服务 - 多渠道接入
├── admin-service (8006)   # 管理服务 - 系统管理+坐席服务
└── analytics-service (8007) # 分析服务 - 数据统计
```

## 快速开始

### 环境要求
- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- ChromaDB

### 启动服务

```bash
# 启动 API Gateway (8080)
cd api-gateway
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# （在另一个终端）启动用户服务 (8001)
cd ../user-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# （在另一个终端）启动聊天服务 (8002)
cd ../chat-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# （在另一个终端）启动知识库服务 (8003)
cd ../knowledge-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

### 验证服务

```bash
# 健康检查
curl http://localhost:8080/health

# API文档
open http://localhost:8080/docs
```

## 主要功能

- 🔐 用户认证与授权（JWT + bcrypt）
- 🤖 RAG智能问答（SSE流式输出、打字机效果）
- 📚 知识库管理（文档上传、分块、向量化）
- 🔒 防提示词注入（多层检测机制）
- 💬 多渠道接入
- ⚠️ 告警管理
- 👥 多租户支持（企业数据完全隔离）
- 🔄 混合搜索（语义+关键词搜索混合召回）
- 📊 数据统计与分析
- 🎧 企业级客服坐席系统
  - 坐席登录认证（OAuth2）
  - 会话接入与管理
  - WebSocket实时通知
  - 会话优先级管理
  - 坐席状态监控

## 安全特性

- ✅ 防SQL注入（SQLAlchemy ORM）
- ✅ 防提示词注入（关键词+正则+语义三层检测）
- ✅ API限流（Redis实现IP级别限流）
- ✅ CORS保护
- ✅ JWT认证
- ✅ 敏感词检测
- ✅ 企业数据隔离

## API文档

启动服务后访问：`http://localhost:8080/docs`

## 目录结构

```
backend/
├── api-gateway/           # API网关
│   ├── main.py         # 网关入口
│   ├── config.py
│   ├── security.py       # JWT验证
│   └── redis_client.py
├── user-service/         # 用户服务
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── crud.py
├── chat-service/         # 聊天服务
│   ├── main.py
│   ├── models.py
│   ├── rag.py            # RAG检索
│   ├── llm.py            # LLM调用
│   ├── intent_router.py
│   ├── sensitive.py
│   ├── prompt_injection_defender.py
│   └── sse_stream.py
├── knowledge-service/    # 知识库服务
│   ├── main.py
│   ├── models.py
│   ├── vector_store.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── faq_engine.py
│   └── rerank.py
├── alert-service/       # 告警服务
├── channel-service/     # 渠道服务
├── admin-service/       # 管理服务 - 运营仪表盘、坐席服务、WebSocket实时更新
│   ├── main.py          # 坐席API、管理API、WebSocket
│   ├── config.py
│   ├── database.py
│   └── models.py        # Agent、AgentSession模型
├── analytics-service/  # 分析服务 - 数据统计
├── common/             # 公共模块
├── tests/              # 测试文件
└── docs/               # 文档
```

## 开发指南

### 运行测试

```bash
cd backend/tests

# 运行调试脚本
python debug_services.py
```

### 添加新服务

1. 创建新的服务目录
2. 添加 requirements.txt
3. 添加 Dockerfile
4. 在API Gateway添加路由
5. 更新配置文件

## 文档

- [产品文档](./docs/产品经理视角-项目整合说明文档.md)
- [API规范](./docs/API_SPECIFICATION.md)
- [架构文档](./docs/ARCHITECTURE_FINAL.md)
- [部署指南](./docs/DEPLOYMENT_GUIDE.md)
- [学习教程](./learning/README.md)
- [安全检查报告](./tests/security-check-report.md)

## 许可证

MIT License
