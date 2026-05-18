# 后端部署指南

## 环境要求

- Python >= 3.9
- PostgreSQL >= 14
- Redis >= 6
- Docker & Docker Compose (可选)

## 快速部署

### 使用 Docker Compose

```bash
cd backend

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api-gateway
```

### 手动部署

#### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 2. 配置环境变量

创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/rag_db

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# JWT 配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM 配置
OPENAI_API_KEY=sk-your-api-key
LLM_PROVIDER=openai

# 向量数据库
CHROMA_DB_PATH=./data/chroma_db
```

#### 3. 启动服务

```bash
# 启动 API Gateway
cd api-gateway
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# 启动其他微服务 (可选)
cd ../chat-service && uvicorn main:app --port 8081 &
cd ../user-service && uvicorn main:app --port 8082 &
cd ../knowledge-service && uvicorn main:app --port 8083 &
```

## 微服务架构

```
┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│ API Gateway │
└─────────────┘     └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │  User   │       │  Chat   │       │Knowledge│
   │ Service │       │ Service │       │ Service │
   └────┬────┘       └────┬────┘       └────┬────┘
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │PostgreSQL│      │ Redis   │       │ ChromaDB│
   └─────────┘       └─────────┘       └─────────┘
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| API Gateway | 8080 | 主入口 |
| User Service | 8081 | 用户认证 |
| Chat Service | 8082 | 聊天处理 |
| Knowledge Service | 8083 | 知识库 |

## 健康检查

```bash
# API Gateway 健康检查
curl http://localhost:8080/health

# 服务状态检查
curl http://localhost:8080/api/v1/health
```

## 日志查看

```bash
# API Gateway 日志
tail -f logs/api-gateway.log

# 所有服务日志
docker-compose logs -f
```

## 常见问题

### 1. 数据库连接失败

确保 PostgreSQL 已启动：

```bash
# 检查 PostgreSQL
pg_isready -h localhost -p 5432
```

### 2. Redis 连接失败

```bash
# 检查 Redis
redis-cli ping
```

### 3. LLM API 调用失败

检查 API Key 配置：

```bash
echo $OPENAI_API_KEY
```

### 4. 端口冲突

修改 `docker-compose.yml` 中的端口映射。

## 生产环境优化

### 1. 使用 Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### 2. 配置 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name api.your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 启用 HTTPS

使用 Let's Encrypt 或其他证书：

```bash
certbot --nginx -d api.your-domain.com
```

## 监控和日志

### 集成 Prometheus

```yaml
# docker-compose.yml 添加
metrics:
  image: prom/prometheus
  ports:
    - "9090:9090"
```

### 查看 Metrics

```bash
curl http://localhost:8080/metrics
```

## 备份和恢复

### 数据库备份

```bash
pg_dump -U user -d rag_db > backup.sql
```

### 恢复数据

```bash
psql -U user -d rag_db < backup.sql
```
