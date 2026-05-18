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
- **部署**: Docker Compose

## 微服务架构

```
后端服务
├── api-gateway (8080)      # API网关 - 统一入口
├── user-service (8001)     # 用户服务 - 认证、企业管理
├── chat-service (8002)     # 聊天服务 - RAG问答、流式输出
├── knowledge-service (8003) # 知识库服务 - 文档管理、向量化
├── alert-service (8004)    # 告警服务 - 敏感内容告警
├── channel-service (8005)  # 渠道服务 - 多渠道接入
├── admin-service (8006)   # 管理服务 - 系统管理API
└── analytics-service (8007) # 分析服务 - 数据统计
```

## 快速开始

### 环境要求
- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- ChromaDB

### 安装依赖

```bash
cd backend
pip install -r api-gateway/requirements.txt
```

### 启动服务

```bash
# 启动API网关
cd api-gateway
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
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
├── alert-service/        # 告警服务
├── channel-service/      # 渠道服务
├── admin-service/        # 管理服务 - 运营仪表盘、WebSocket实时更新
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── models.py
├── analytics-service/  # 分析服务 - 数据统计
├── common/             # 公共模块
├── tests/              # 测试文件
├── docs/               # 文档
└── README.md
```

## 开发指南

### 运行测试

```bash
cd backend/tests

# 运行所有后端测试
python -m pytest -v

# 运行特定测试文件
python test_api_gateway.py
python test_chat_service.py
python test_user_service.py
python test_knowledge_service.py

# 启动服务调试器
python debug_services.py
```

### 添加新服务

1. 创建新的服务目录
2. 添加 requirements.txt
3. 添加 Dockerfile
4. 在API Gateway添加路由
5. 更新配置文件

---

## 前后端联合调试

### 前置条件

1. 确保已克隆两个仓库：
   - 前端：`https://github.com/BH3PHW/rag-agent-frontend`
   - 后端：`https://github.com/BH3PHW/rag-customer-service`

2. 确保环境变量已正确配置

### 后端启动步骤

#### 1. 启动后端服务

**方式一：使用单独启动 API Gateway（推荐用于开发调试）**
```bash
cd backend/api-gateway
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

**方式二：启动所有微服务
```bash
# 启动 API Gateway (8080)
cd api-gateway && uvicorn main:app --port 8080 --reload &

# 启动用户服务 (8001)
cd ../user-service && uvicorn main:app --port 8001 --reload &

# 启动聊天服务 (8002)
cd ../chat-service && uvicorn main:app --port 8002 --reload &

# 启动知识库服务 (8003)
cd ../knowledge-service && uvicorn main:app --port 8003 --reload &

# 启动管理服务 (8006) - 运营仪表盘
cd ../admin-service && uvicorn main:app --port 8006 --reload &
```

#### 2. 验证后端服务

```bash
# 健康检查
curl http://localhost:8080/health

# API文档
open http://localhost:8080/docs
```

### 前端启动步骤

#### 1. 安装前端环境准备

```bash
# 进入前端项目根目录
cd frontend

# 安装依赖
npm install
```

#### 2. 配置前端API地址

编辑环境变量或配置文件，确保指向本地后端：

```env
# 消费者端、企业端、系统管理端
# 默认配置文件: apps/[app-name/src/api/client.ts
const API_BASE_URL = 'http://localhost:8080'
```

#### 3. 启动前端应用

**启动消费者端 (3001)**
```bash
cd apps/consumer
npm run dev
```

**启动企业端 (3002)**
```bash
cd apps/enterprise
npm run dev
```

**启动系统管理端 (3003)**
```bash
cd apps/system-admin
npm run dev
```

### 使用联合调试脚本

#### 运行完整联合调试 (推荐方式

使用后端调试脚本 (位于`tests/api-debug.js
```bash
cd tests
node api-debug.js --all
```

**调试输出包含内容包括：
- 46个API端点验证
- 前后端API匹配检查
- 流式输出测试
- 安全功能测试
- 知识库功能测试

**调试步骤:**
1. 启动后端和前端服务后，访问：
- 消费者端: http://localhost:3001
- 企业管理端: http://localhost:3002
- 系统管理端: http://localhost:3003
- API文档: http://localhost:8080/docs

---

## 前后端联合部署

### 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                    负载均衡 (Nginx/Cloudflare)              │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
  ┌───────▼───────┐   ┌──────▼───────┐
  │   前端服务器  │   │  后端服务器  │
  │ (Vercel/Nginx│   │ (Docker)   │
  └───────┬───────┘   └──────┬───────┘
          │                  │
  ┌───────┴───────┐   ┌──────▼───────┐
  │ 消费者端 3001  │   │ API GW 8080  │
  │ 企业端 3002    │   │ 微服务集群  │
  │ 管理端 3003    │   └─────────────┘
  └───────────────┘
```

### 环境变量配置（生产环境）

#### 后端环境变量
创建`.env`
```env
# 数据库
DATABASE_URL=postgresql://user:pass@db/rag_db
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-production-secret-key

# LLM
OPENAI_API_KEY=sk-xxx

# 安全
CORS_ORIGINS=["https://your-domain.com"]
```

#### 前端环境变量
创建`.env.production`
```env
NEXT_PUBLIC_API_BASE_URL=https://api.your-domain.com
NEXT_PUBLIC_APP_ENV=production
```

### Docker Compose 部署方案

#### 后端部署

```bash
# 后端
cd backend
docker-compose up -d
```

#### 前端部署
```bash
cd frontend
# 构建所有应用
npm run build

# 使用 nginx/或者部署到 Vercel
```

### Nginx 配置示例

**前端 Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 消费者端
    location / {
        root /path/to/frontend/apps/consumer/dist;
        try_files $uri $uri/ /index.html;
    }

    # 企业端
    location /enterprise {
        alias /path/to/frontend/apps/enterprise/dist;
        try_files $uri $uri/ /enterprise/index.html;
    }

    # 管理端
    location /admin {
        alias /path/to/frontend/apps/system-admin/dist;
        try_files $uri $uri/ /admin/index.html;
    }

    # API反向代理到后端
    location /api {
        proxy_pass http://backend-server:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 部署验证清单

- [ ] 后端服务健康检查通过
- [ ] API文档可访问
- [ ] 前端所有功能正常
- [ ] 数据库连接正常
- [ ] Redis连接正常
- [ ] LLM API调用正常
- [ ] 向量数据库正常
- [ ] 安全配置正确
- [ ] HTTPS证书配置
- [ ] 监控和日志正常

---

## 文档

- [产品文档](./docs/产品经理视角-项目整合说明文档.md)
- [API规范](./docs/API_SPECIFICATION.md)
- [架构文档](./docs/ARCHITECTURE_FINAL.md)
- [部署指南](./docs/DEPLOYMENT_GUIDE.md)
- [学习教程](./learning/README.md)
- [联合调试报告](./tests/api-joint-debug-report.md)
- [安全检查报告](./tests/security-check-report.md)

## 许可证

MIT License
