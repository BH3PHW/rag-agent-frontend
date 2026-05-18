# RAG 智能客服系统 - 完整部署文档

## 📋 文档概述

本文档提供 RAG 智能客服系统的完整部署指南，包括：
- 系统架构说明
- 环境要求
- 前后端部署步骤
- Docker 部署
- 运维指南
- 故障排查

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                      用户层                              │
├──────────────┬──────────────┬───────────────────────────┤
│  消费者端    │   企业前端   │      系统管理前端           │
│  Widget      │  管理控制台   │      系统管理员            │
│  (Port 3000) │  (Port 8080) │      (Port 9090)          │
└──────┬───────┴──────┬───────┴────────────┬──────────────┘
       │              │                     │
       │              │                     │
       └──────────────┼─────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │     API Gateway        │
         │      (Port 8000)       │
         └────────────┬───────────┘
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
┌────────────┐  ┌──────────┐  ┌──────────────┐
│Chat Service│  │Channel   │  │Knowledge     │
│Port 8001   │  │Service   │  │Service       │
│            │  │Port 8002 │  │Port 8003     │
└────────────┘  └──────────┘  └──────────────┘
       │              │              │
       │              │              │
       └──────────────┼──────────────┘
                      │
         ┌────────────────────────┐
         │   PostgreSQL + Redis   │
         │   + ChromaDB Vector DB │
         └────────────────────────┘
```

---

## 📦 项目结构

```
backend-rag-customer-service/
│
├── frontend/                      # 前端应用
│   ├── consumer/                 # 消费者前端
│   ├── enterprise/              # 企业前端
│   └── system-admin/            # 系统管理前端
│
├── backend/                      # 后端服务
│   ├── api-gateway/             # API 网关
│   ├── chat-service/            # 聊天服务
│   ├── channel-service/         # 渠道接入服务
│   ├── knowledge-service/        # 知识库服务
│   ├── user-service/            # 用户服务
│   ├── admin-console-api/       # 管理后台 API
│   └── common/                  # 公共模块
│
├── docker-compose.yml            # Docker 编排配置
├── deploy.sh                    # 一键部署脚本
├── .env.example                 # 环境变量示例
└── docs/                        # 文档目录
```

---

## 🚀 环境要求

### 硬件要求

| 环境 | CPU | 内存 | 磁盘 | 说明 |
|------|-----|------|------|------|
| 开发环境 | 2核 | 4GB | 20GB | 单机部署 |
| 生产环境 | 4核 | 8GB | 50GB | 推荐配置 |
| 高可用环境 | 8核 | 16GB | 100GB | 集群部署 |

### 软件要求

- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / macOS 12+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.10+ (本地开发)
- **Node.js**: 16+ (可选，前端构建)

---

## 📥 安装步骤

### 方式一：Docker 部署（推荐）

#### 1. 克隆项目

```bash
git clone https://your-repo/rag-customer-service.git
cd rag-customer-service
```

#### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/rag_db
REDIS_URL=redis://localhost:6379/0

# LLM 配置
OPENAI_API_KEY=sk-your-api-key
LLM_PROVIDER=openai

# 企业配置
DEFAULT_ENTERPRISE_ID=enterprise-001

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret

# 服务端口
GATEWAY_PORT=8000
ADMIN_API_PORT=8080
```

#### 3. 一键启动

```bash
chmod +x deploy.sh
./deploy.sh
```

#### 4. 验证服务

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api-gateway
```

---

### 方式二：本地开发部署

#### 1. 安装依赖

```bash
# Python 依赖
pip install -r requirements.txt

# 安装后端服务依赖
cd backend/api-gateway && pip install -r requirements.txt
cd backend/chat-service && pip install -r requirements.txt
# ... 其他服务
```

#### 2. 启动数据库服务

```bash
# 使用 Docker 启动数据库
docker run -d \
  --name rag-postgres \
  -e POSTGRES_DB=rag_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:15

docker run -d \
  --name rag-redis \
  -p 6379:6379 \
  redis:7
```

#### 3. 启动后端服务

```bash
# 启动 API Gateway
cd backend/api-gateway
uvicorn main:app --host 0.0.0.0 --port 8000

# 新终端 - 启动管理后台 API
cd backend/admin-console-api
uvicorn main:app --host 0.0.0.0 --port 8080
```

#### 4. 启动前端服务

```bash
# 终端 1 - 消费者前端
cd frontend/consumer
python3 -m http.server 3000

# 终端 2 - 企业前端
cd frontend/enterprise
python3 -m http.server 8080

# 终端 3 - 系统管理前端
cd frontend/system-admin
python3 -m http.server 9090
```

---

## 🌐 服务访问地址

部署完成后，访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| 消费者 Widget 演示 | http://localhost:3000 | 用户端对话演示 |
| 企业管理控制台 | http://localhost:8080 | 企业运营管理 |
| 系统管理后台 | http://localhost:9090 | 平台系统管理 |
| API Gateway | http://localhost:8000 | API 文档 |
| 管理 API 文档 | http://localhost:8080/docs | Swagger 文档 |

---

## 🔧 核心功能部署

### 1. 消费者 Widget 嵌入指南

#### 步骤 1：获取嵌入代码

在企业管理控制台（http://localhost:8080）的「渠道接入」页面，可以生成专属的嵌入代码。

#### 步骤 2：嵌入网站

将以下代码添加到您的网站 `</body>` 标签前：

```html
<!-- RAG 智能客服 Widget -->
<script src="http://your-domain.com/consumer/widget.js"></script>
<script>
  RAGWidget.init({
    enterpriseId: 'your-enterprise-id',
    apiBaseUrl: 'http://your-api-server.com',
    icon: '💬'
  });
</script>
```

#### 步骤 3：配置域名白名单

在企业管理控制台配置允许嵌入的域名。

---

### 2. 微信公众号接入

#### 步骤 1：获取微信公众号配置信息

- AppID
- AppSecret
- Token
- EncodingAESKey

#### 步骤 2：在控制台配置

登录企业管理控制台 → 「渠道接入」→ 「微信公众号」

填写上述配置信息。

#### 步骤 3：配置微信后台

登录微信公众平台 → 基本配置 → 服务器配置：

- URL: `http://your-domain.com/api/v1/channel/{enterprise_id}/wechat/webhook`
- Token: 与步骤 1 一致
- EncodingAESKey: 与步骤 1 一致
- 消息加密方式: 推荐使用安全模式

---

### 3. 知识库配置

#### 上传文档

1. 登录企业管理控制台
2. 进入「知识库管理」
3. 点击「上传文档」
4. 支持格式：PDF、TXT、DOCX、Markdown

#### 配置匹配规则

```json
{
  "match_threshold": 0.75,
  "max_chunks": 5,
  "rerank_enabled": true
}
```

---

## 🔒 安全配置

### 1. API 密钥管理

```bash
# 生成新的 API 密钥
openssl rand -hex 32
```

### 2. 配置 HTTPS（生产环境）

```nginx
# /etc/nginx/sites-available/rag-service
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    # API Gateway
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 前端静态文件
    location / {
        root /var/www/rag-frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

### 3. 防火墙配置

```bash
# 开放必要端口
sudo ufw allow 3000/tcp   # 消费者前端
sudo ufw allow 8080/tcp   # 企业前端
sudo ufw allow 9090/tcp   # 系统管理前端
sudo ufw allow 8000/tcp   # API Gateway

# 只在必要时开放数据库端口
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp
```

---

## 📊 运维监控

### 查看服务日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f api-gateway
docker-compose logs -f chat-service

# 查看错误日志
docker-compose logs | grep ERROR
```

### 健康检查

```bash
# API Gateway 健康检查
curl http://localhost:8000/health

# 管理 API 健康检查
curl http://localhost:8080/health

# 数据库连接检查
docker exec -it rag-postgres psql -U postgres -d rag_db -c "SELECT 1;"
```

### 性能监控

建议使用以下工具监控：

- **Prometheus + Grafana**: 性能指标监控
- **ELK Stack**: 日志收集和分析
- **Sentry**: 错误追踪

---

## 🐛 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 检查端口占用
sudo netstat -tlnp | grep 8080

# 查看详细错误
docker-compose logs service-name
```

#### 2. 数据库连接失败

```bash
# 检查数据库容器
docker ps | grep postgres

# 重启数据库
docker-compose restart postgres
```

#### 3. 前端无法连接后端

```bash
# 检查 CORS 配置
# 确保 API Gateway 配置了正确的 CORS 策略

# 检查网络连通性
curl http://localhost:8000/health
```

#### 4. WebSocket 连接失败

```bash
# 检查 Nginx WebSocket 支持
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

---

## 🔄 更新升级

### 版本升级步骤

```bash
# 1. 备份数据
docker-compose exec postgres pg_dump -U postgres rag_db > backup_$(date +%Y%m%d).sql

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建
docker-compose build

# 4. 重启服务
docker-compose down
docker-compose up -d
```

---

## 📞 技术支持

如遇到问题，请检查：

1. **官方文档**: https://docs.example.com
2. **问题反馈**: https://github.com/your-repo/issues
3. **联系邮箱**: support@example.com

---

## 📄 附录

### A. Docker Compose 完整配置

详见项目根目录 `docker-compose.yml` 文件。

### B. 环境变量完整列表

详见项目根目录 `.env.example` 文件。

### C. API 接口文档

部署完成后访问：
- API Gateway: http://localhost:8000/docs
- 管理后台 API: http://localhost:8080/docs

---

**文档版本**: v2.2.0  
**最后更新**: 2024-05-18  
**维护团队**: RAG 智能客服开发团队
