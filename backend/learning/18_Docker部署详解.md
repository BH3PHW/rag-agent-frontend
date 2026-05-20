# 第10章：Docker 容器化部署与生产实践

> 🎯 **学习目标**：掌握Docker容器化部署，理解生产环境最佳实践
> 💡 **工程化思维**：环境一致性、可复制部署、可扩展架构
> 💡 **产品化思维**：高可用、快速扩容、灾备能力

---

## 18.1 为什么选择Docker？

### 18.1.1 传统部署问题

```
传统部署的痛点：
┌────────────────────────────────────────────────────────────┐
│  1. 环境不一致                                              │
│     "我本地可以运行啊？" → 线上环境依赖不一致             │
│                                                           │
│  2. 部署复杂                                               │
│     "我要装Python、Node、Redis、PostgreSQL..." → 很耗时   │
│                                                           │
│  3. 迁移困难                                               │
│     "这个服务器要迁移？" → 重新搞一次，太麻烦             │
│                                                           │
│  4. 扩缩容困难                                             │
│     "突然有1000人同时在线怎么办？" → 手动扩容太麻烦        │
└────────────────────────────────────────────────────────────┘

Docker解决的问题：
┌────────────────────────────────────────────────────────────┐
│  1. 一次打包，到处运行                                       │
│     "这是镜像，你拿去直接运行" → 环境一致                  │
│                                                           │
│  2. 一键部署                                               │
│     "docker-compose up" → 服务全起来                       │
│                                                           │
│  3. 快速扩容                                               │
│     "容器复制多个就行" → 水平扩展                          │
└────────────────────────────────────────────────────────────┘
```

---

## 18.2 镜像构建 - Dockerfile详解

### 18.2.1 后端服务镜像构建

```dockerfile
# 文件：backend/chat-service/Dockerfile

# 工程化：多阶段构建，减小镜像大小
# 阶段1：构建阶段
FROM python:3.11-slim as builder

WORKDIR /build

# 工程化：先复制依赖，利用缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 阶段2：运行阶段
FROM python:3.11-slim

WORKDIR /app

# 工程化：创建非root用户运行，安全第一
RUN useradd -m -u 1000 appuser

# 从构建阶段复制依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# 复制应用代码
COPY . .

# 工程化：设置权限
RUN chown -R appuser:appuser /app
USER appuser

# 工程化：环境变量配置
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=info

# 暴露端口
EXPOSE 8002

# 工程化：健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 18.2.2 前端应用镜像构建

```dockerfile
# 文件：frontend/Dockerfile

# 工程化：多阶段构建，减小镜像
# 阶段1：构建阶段
FROM node:20-alpine as builder

WORKDIR /build

# 工程化：先复制package.json，利用缓存
COPY package*.json ./
RUN npm ci

# 复制代码并构建
COPY . .
RUN npm run build

# 阶段2：Nginx运行阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /build/dist /usr/share/nginx/html

# 工程化：Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 工程化：健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 18.2.3 Nginx配置

```nginx
# 文件：frontend/nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # 工程化：Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml;
    
    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;
        
        # 工程化：前端路由支持（SPA刷新问题）
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # 工程化：API代理
        location /api {
            proxy_pass http://api-gateway:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            
            # SSE流式响应需要的配置
            proxy_buffering off;
            proxy_cache off;
            proxy_set_header Connection '';
            proxy_http_version 1.1;
        }
        
        # 工程化：静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

---

## 18.3 Docker Compose - 多服务编排

### 18.3.1 完整的docker-compose.yml

```yaml
# 文件：docker-compose.yml
version: '3.8'

# 工程化：网络隔离
networks:
  rag-network:
    driver: bridge

# 工程化：数据卷持久化
volumes:
  postgres-data:
  redis-data:
  chroma-data:

services:
  # 数据库服务
  postgres:
    image: postgres:15-alpine
    container_name: rag-postgres
    environment:
      POSTGRES_USER: rag
      POSTGRES_PASSWORD: ragpassword
      POSTGRES_DB: rag_system
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - rag-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rag"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: rag-redis
    command: redis-server --requirepass redispassword
    volumes:
      - redis-data:/data
    networks:
      - rag-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "redispassword", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  # Chroma向量数据库
  chroma:
    image: chromadb/chroma:0.4.18
    container_name: rag-chroma
    volumes:
      - chroma-data:/chroma/chroma
    networks:
      - rag-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # 后端服务 - API网关
  api-gateway:
    build: ./backend/api-gateway
    container_name: rag-api-gateway
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PASSWORD=redispassword
      - POSTGRES_HOST=postgres
      - POSTGRES_PASSWORD=ragpassword
    networks:
      - rag-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # 后端服务 - 用户服务
  user-service:
    build: ./backend/user-service
    container_name: rag-user-service
    ports:
      - "8001:8001"
    environment:
      - REDIS_HOST=redis
      - REDIS_PASSWORD=redispassword
      - POSTGRES_HOST=postgres
      - POSTGRES_PASSWORD=ragpassword
    networks:
      - rag-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # 后端服务 - 聊天服务
  chat-service:
    build: ./backend/chat-service
    container_name: rag-chat-service
    ports:
      - "8002:8002"
    environment:
      - REDIS_HOST=redis
      - REDIS_PASSWORD=redispassword
      - CHROMA_HOST=chroma
    networks:
      - rag-network
    depends_on:
      redis:
        condition: service_healthy
      chroma:
        condition: service_healthy
    restart: unless-stopped

  # 后端服务 - 知识库服务
  knowledge-service:
    build: ./backend/knowledge-service
    container_name: rag-knowledge-service
    ports:
      - "8003:8003"
    environment:
      - REDIS_HOST=redis
      - REDIS_PASSWORD=redispassword
      - CHROMA_HOST=chroma
    networks:
      - rag-network
    depends_on:
      redis:
        condition: service_healthy
      chroma:
        condition: service_healthy
    restart: unless-stopped

  # 前端应用 - 用户端
  consumer-frontend:
    build: ./frontend
    container_name: rag-consumer-frontend
    ports:
      - "3001:80"
    networks:
      - rag-network
    depends_on:
      - api-gateway
    restart: unless-stopped

  # 前端应用 - 企业管理端
  enterprise-frontend:
    build: ./frontend
    container_name: rag-enterprise-frontend
    ports:
      - "3002:80"
    networks:
      - rag-network
    depends_on:
      - api-gateway
    restart: unless-stopped
```

### 18.3.2 工程化配置要点

| 配置项 | 作用 | 工程化价值 |
|--------|------|-----------|
| networks | 网络隔离 | 安全性、通信优化 |
| volumes | 数据持久化 | 数据不丢失、可迁移 |
| healthcheck | 健康检查 | 自动发现服务异常 |
| depends_on | 依赖关系 | 按顺序启动 |
| restart | 自动重启 | 高可用 |
| environment | 环境配置 | 配置分离 |

---

## 18.4 生产环境部署 - 高可用架构

### 18.4.1 生产环境架构

```
生产环境推荐架构：
┌──────────────────────────────────────────────────────────────────┐
│                          负载均衡层                                 │
│                         Nginx/HAProxy                                │
└────────────────────────┬───────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
   ┌─────▼─────┐                   ┌─────▼─────┐
   │   App1    │                   │   App2    │ ← 多实例高可用
   │ (Docker)  │                   │ (Docker)  │
   └───────────┘                   └───────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
   ┌─────────────────────┴─────────────────────┐
   │                                           │
┌──▼────────┐    ┌─────────┐     ┌──────────┐
│ PostgreSQL│    │  Redis  │    │  Chroma  │
│ (主从)    │    │ (哨兵)  │    │ (集群)   │
└───────────┘    └─────────┘     └──────────┘
```

### 18.4.2 环境变量管理 - .env文件

```env
# 文件：.env

# 数据库配置
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=rag
POSTGRES_PASSWORD=your_secure_password_change_this
POSTGRES_DB=rag_system

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_redis_password
REDIS_DB=0

# 应用配置
LOG_LEVEL=info
DEBUG=false

# LLM配置
OPENAI_API_KEY=sk-your-api-key
LLM_MODEL=gpt-3.5-turbo
```

---

## 18.5 常用Docker命令 - 工程化操作

### 18.5.1 开发阶段

```bash
# 构建并启动
docker-compose up --build -d

# 查看日志
docker-compose logs -f
docker-compose logs -f chat-service  # 查看特定服务日志

# 进入容器
docker-compose exec chat-service bash

# 重启服务
docker-compose restart chat-service

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 18.5.2 生产部署

```bash
# 拉取最新镜像
docker-compose pull

# 滚动更新（零停机）
docker-compose up -d --no-deps --build chat-service

# 查看服务状态
docker-compose ps

# 查看资源使用情况
docker stats

# 清理未使用资源
docker system prune -a
```

---

## 18.6 Docker监控与日志 - 可观测性

### 18.6.1 日志收集

```yaml
# 工程化：日志驱动配置
services:
  chat-service:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"    # 单个日志最大10MB
        max-file: "3"     # 保留3个日志文件
```

### 18.6.2 监控堆栈

```yaml
# 可选：添加Prometheus监控
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 18.7 本章小结

### Docker核心概念

| 概念 | 作用 |
|------|------|
| **Dockerfile** | 定义镜像构建过程 |
| **镜像(Image)** | 应用的打包形式 |
| **容器(Container)** | 镜像的运行实例 |
| **Docker Compose** | 多服务编排 |
| **Volume** | 数据持久化 |

### 工程化思维要点

1. **多阶段构建** - 减小镜像大小
2. **非Root用户** - 安全运行
3. **健康检查** - 服务可观测
4. **环境配置分离** - 配置不硬编码
5. **日志轮转** - 磁盘空间管理
6. **监控告警** - 及时发现问题

### 产品化思维要点

1. **高可用** - 多实例、自动重启
2. **快速扩容** - 容器复制、负载均衡
3. **数据安全** - 持久化、备份策略
4. **快速部署** - 一键部署、回滚

### 下一步学习

- [19_数据清洗与预处理.md](./19_数据清洗与预处理.md) - 学习数据处理
