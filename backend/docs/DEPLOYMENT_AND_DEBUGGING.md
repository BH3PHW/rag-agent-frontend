# 前后端联合调试与部署指南

## 目录

1. [环境要求](#1-环境要求)
2. [依赖版本](#2-依赖版本)
3. [环境搭建](#3-环境搭建)
4. [开发调试](#4-开发调试)
5. [生产部署](#5-生产部署)
6. [验证检查](#6-验证检查)

---

## 1. 环境要求

### 硬件要求
- CPU: 4核以上
- 内存: 8GB以上
- 存储: 50GB以上可用空间

### 软件要求
- Linux/macOS/Windows (建议 Linux 或 macOS)
- Git (版本控制)
- Docker & Docker Compose (可选，用于容器化部署)

---

## 2. 依赖版本

### 后端依赖

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| FastAPI | 0.100+ | Web框架 |
| SQLAlchemy | 2.0+ | ORM |
| Uvicorn | 0.23+ | ASGI服务器 |
| redis-py | 5.0+ | Redis客户端 |
| python-jose | 3.3+ | JWT认证 |
| passlib | 1.7+ | 密码加密 |
| httpx | 0.25+ | HTTP客户端 |
| chromadb | 0.4+ | 向量数据库 |

### 前端依赖

| 依赖 | 版本 | 说明 |
|------|------|------|
| Node.js | 18+ | JavaScript运行时 |
| npm | 9+ | 包管理器 |
| React | 18+ | 前端框架 |
| TypeScript | 5+ | 类型检查 |
| Vite | 5+ | 构建工具 |
| Tailwind CSS | 3+ | CSS框架 |
| Zustand | 4+ | 状态管理 |
| Lucide React | 0.265+ | 图标库 |

### 数据库依赖

| 服务 | 版本 | 说明 |
|------|------|------|
| PostgreSQL | 14+ | 关系型数据库 |
| Redis | 6+ | 缓存服务 |
| ChromaDB | 0.4+ | 向量数据库 |

---

## 3. 环境搭建

### 3.1 克隆项目

```bash
# 克隆项目
git clone <repository-url>
cd workspace
```

### 3.2 后端环境配置

#### 安装 Python 依赖

```bash
cd backend

# 安装 API Gateway 依赖
cd api-gateway
pip install -r requirements.txt

# 安装 User Service 依赖
cd ../user-service
pip install -r requirements.txt

# 安装 Chat Service 依赖
cd ../chat-service
pip install -r requirements.txt

# 安装 Knowledge Service 依赖
cd ../knowledge-service
pip install -r requirements.txt

# 安装 Admin Service 依赖
cd ../admin-service
pip install -r requirements.txt
```

#### 配置数据库连接

在各服务的 `config.py` 中配置数据库连接：

```python
# config.py 示例
DATABASE_URL = "postgresql://user:password@localhost:5432/rag_db"
REDIS_URL = "redis://localhost:6379/0"
```

### 3.3 前端环境配置

```bash
cd frontend

# 安装所有依赖
npm install
```

#### 配置环境变量

创建 `.env` 文件（各应用目录）：

```env
# apps/consumer/.env
VITE_API_BASE_URL=http://localhost:8080
VITE_APP_ENV=development

# apps/enterprise/.env  
VITE_API_BASE_URL=http://localhost:8080
VITE_APP_ENV=development

# apps/system-admin-portal/.env
VITE_API_BASE_URL=http://localhost:8080
VITE_APP_ENV=development
```

---

## 4. 开发调试

### 4.1 启动后端服务

**方式一：使用终端分别启动**

```bash
# 终端1: 启动 API Gateway (8080)
cd backend/api-gateway
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# 终端2: 启动 User Service (8001)
cd backend/user-service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 终端3: 启动 Chat Service (8002)
cd backend/chat-service
uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# 终端4: 启动 Knowledge Service (8003)
cd backend/knowledge-service
uvicorn main:app --host 0.0.0.0 --port 8003 --reload

# 终端5: 启动 Admin Service (8006)
cd backend/admin-service
uvicorn main:app --host 0.0.0.0 --port 8006 --reload
```

### 4.2 启动前端应用

```bash
# 终端1: 消费者端 (3001)
cd frontend/apps/consumer
npm run dev

# 终端2: 企业端 (3002)
cd frontend/apps/enterprise
npm run dev

# 终端3: 系统管理端 (3003)
cd frontend/apps/system-admin-portal
npm run dev
```

### 4.3 API 调试

#### 测试认证接口

```bash
# 注册用户
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# 登录
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

#### 测试聊天接口

```bash
# 创建会话
curl -X POST http://localhost:8080/api/v1/chat/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"user_id": "<user-id>", "enterprise_id": "<enterprise-id>"}'

# 发送消息（流式）
curl -X POST http://localhost:8080/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"message": "你好", "enterprise_id": "<enterprise-id>"}'
```

### 4.4 调试脚本

使用测试脚本进行自动化调试：

```bash
cd backend/tests

# 运行调试脚本
python debug_services.py
```

---

## 5. 生产部署

### 5.1 后端部署

#### 使用 Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: rag_db
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: rag_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - chroma_data:/chroma/chroma
    ports:
      - "8000:8000"

  api-gateway:
    build: ./api-gateway
    environment:
      DATABASE_URL: postgresql://rag_user:rag_password@postgres:5432/rag_db
      REDIS_URL: redis://redis:6379/0
      CHROMA_URL: http://chromadb:8000
    ports:
      - "8080:8080"
    depends_on:
      - postgres
      - redis
      - chromadb

  user-service:
    build: ./user-service
    environment:
      DATABASE_URL: postgresql://rag_user:rag_password@postgres:5432/rag_db
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis

  chat-service:
    build: ./chat-service
    environment:
      DATABASE_URL: postgresql://rag_user:rag_password@postgres:5432/rag_db
      REDIS_URL: redis://redis:6379/0
      CHROMA_URL: http://chromadb:8000
    ports:
      - "8002:8002"
    depends_on:
      - postgres
      - redis
      - chromadb

  knowledge-service:
    build: ./knowledge-service
    environment:
      DATABASE_URL: postgresql://rag_user:rag_password@postgres:5432/rag_db
      REDIS_URL: redis://redis:6379/0
      CHROMA_URL: http://chromadb:8000
    ports:
      - "8003:8003"
    depends_on:
      - postgres
      - redis
      - chromadb

volumes:
  postgres_data:
  redis_data:
  chroma_data:
```

启动服务：

```bash
cd backend
docker-compose up -d
```

### 5.2 前端部署

#### 构建前端应用

```bash
cd frontend

# 构建所有应用
npm run build

# 或构建单个应用
npm run build --workspace=apps/consumer
npm run build --workspace=apps/enterprise
npm run build --workspace=apps/system-admin-portal
```

#### Nginx 配置

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
        try_files $uri $uri/ /index.html;
    }

    # 系统管理端
    location /admin {
        alias /path/to/frontend/apps/system-admin-portal/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 5.3 环境变量配置（生产环境）

#### 后端环境变量

```env
# .env.production
DATABASE_URL=postgresql://user:password@postgres:5432/rag_db
REDIS_URL=redis://redis:6379/0
CHROMA_URL=http://chromadb:8000
JWT_SECRET_KEY=your-production-secret-key
OPENAI_API_KEY=sk-your-api-key
CORS_ORIGINS=["https://your-domain.com"]
LOG_LEVEL=info
```

#### 前端环境变量

```env
# .env.production
VITE_API_BASE_URL=https://api.your-domain.com
VITE_APP_ENV=production
```

---

## 6. 验证检查

### 6.1 后端服务验证

```bash
# 健康检查
curl http://localhost:8080/health

# API 文档
open http://localhost:8080/docs

# 检查数据库连接
curl http://localhost:8080/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

### 6.2 前端应用验证

| 应用 | 地址 | 验证项 |
|------|------|--------|
| 消费者端 | http://localhost:3001 | 聊天窗口能正常打开 |
| 企业端 | http://localhost:3002 | 登录和页面导航正常 |
| 系统管理端 | http://localhost:3003 | 登录和管理功能正常 |

### 6.3 功能验证清单

- [ ] 后端服务健康检查通过
- [ ] API 文档可访问
- [ ] 数据库连接正常
- [ ] Redis 连接正常
- [ ] 向量数据库正常
- [ ] 前端所有功能正常
- [ ] 聊天功能正常工作
- [ ] 流式输出正常
- [ ] 知识库功能正常
- [ ] 认证功能正常
- [ ] HTTPS 证书配置正确
- [ ] 日志与监控正常

---

## 常见问题

### Q: 启动服务时端口被占用？

```bash
# 查找占用端口的进程
lsof -i :8080

# 终止进程
kill -9 <PID>
```

### Q: 数据库连接失败？

1. 检查数据库服务是否启动
2. 确认数据库连接配置正确
3. 检查数据库用户权限

### Q: CORS 错误？

检查后端 CORS 配置，确保前端地址在允许列表中：

```python
# config.py
CORS_ORIGINS = ["http://localhost:3001", "http://localhost:3002", "http://localhost:3003"]
```

---

**版本**: 1.0  
**最后更新**: 2026-05-19
