# RAG 智能客服 - Python 入门教程 4：微服务架构与部署

## 📚 目录
1. [什么是微服务
2. [项目微服务架构详解
3. [Docker与容器化
4. [部署到服务器
5. [调试与问题解决
6. [总结与下一步

---

## 1. 什么是微服务？

### 🏛️ 单体vs微服务

**单体应用（传统方式：
```
一个大程序，把所有功能都塞在一起
┌─────────────────────────────┐
│  一个大程序                  │
│  用户管理、聊天、知识库...   │
└─────────────────────────────┘
```

**微服务（项目的方式：
```
多个小程序，各自独立，互相协作
┌──────┐  ┌──────┐  ┌──────┐
│用户  │  │聊天  │  │知识  │
│服务  │  │服务  │  │库服务│
└───┬──┘  └───┬──┘  └───┬──┘
    │         │         │
    └─────────┴─────────┘
              │
        [API网关]
```

### ✅ 微服务的好处

- **独立开发** - 每个服务可以独立开发
- **独立部署** - 更新一个服务不影响其他
- **技术灵活** - 每个服务可以用不同技术
- **易于扩展** - 热门的服务可以加机器

---

## 2. 项目微服务架构详解

### 🗺️ 完整架构图

```
┌─────────────────────────────────────────────────────────┐
│                      前端层                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │消费者Widget  │ │ 企业管理控制台 │ │ 系统管理后台    │  │
│  │ (3000端口)   │ │  (8080端口)  │ │  (9090端口)      │  │
│  └──────┬───────┘ └───────┬──────┘ └──────┬───────────┘  │
└─────────┼─────────────────┼─────────────────┼───────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                     API网关 (8000端口)                    │
│              [ 统一入口、路由转发、安全 ]                   │
└───────────────────────┬─────────────────────────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    ▼                   ▼                   ▼
┌──────────┐     ┌──────────┐      ┌──────────┐
│聊天服务  │     │渠道服务  │      │知识服务  │
│ (8001)   │     │ (8002)   │      │ (8003)   │
└──────────┘     └──────────┘      └──────────┘
         │                   │
         └─────────┬─────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│PostgreSQL│ │  Redis  │ │ ChromaDB │
└─────────┘ └─────────┘ └──────────┘
```

### 📋 各个服务的作用

| 服务 | 端口 | 作用 |
|------|------|------|
| **API Gateway** | 8000 | 统一入口，路由转发 |
| **Chat Service** | 8001 | 智能对话、流式输出 |
| **Knowledge Service** | 8003 | 知识库、FAQ管理 |
| **Channel Service** | 8005 | 多渠道接入（微信等） |
| **Admin API** | 8080 | 管理后台接口 |

---

## 3. 理解各个服务的功能

### 💬 Chat Service（聊天服务）
路径：`backend/chat-service/`

核心功能：
- 处理聊天消息
- 调用大模型
- 流式输出（打字机效果）
- 敏感内容检测
- 转人工客服

看一下 `backend/chat-service/main.py` 的简化版：

```python
from fastapi import FastAPI

app = FastAPI(title="聊天服务")

# 聊天API（流式输出
@app.post("/api/v1/chat/sessions/{session_id}/messages/stream")
async def chat_stream(session_id: str, message: str):
    """流式聊天API"""
    # 这里是真实聊天逻辑
    pass

# 转人工
@app.post("/api/v1/chat/sessions/{session_id}/escalate")
async def escalate_to_human(session_id: str):
    """转人工客服"""
    pass
```

### 📚 Knowledge Service（知识库服务）
路径：`backend/knowledge-service/`

核心功能：
- 文档上传和分块
- 向量存储
- 语义搜索
- FAQ管理

### 📡 Channel Service（渠道服务）
路径：`backend/channel-service/`

核心功能：
- 微信公众号接入
- 网页Widget接入
- 统一身份管理（OneID
- 差异化消息渲染

---

## 4. Docker与容器化

### 🐳 什么是Docker？

想象一下Docker是一个集装箱，可以把程序和所有需要的东西打包在一起，在哪里运行都一样！

### 📦 Docker基本概念

- **Image（镜像）** - 程序的打包好的模板
- **Container（容器）** - 镜像运行时的实例
- **Dockerfile** - 告诉Docker如何打包的文件

### 🏗️ 看一个项目的Dockerfile

看 `backend/chat-service/Dockerfile`：

```dockerfile
# 从基础镜像开始
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 🤝 Docker Compose（编排工具

看项目根目录的 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  # 数据库服务
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: rag_db
      POSTGRES_PASSWORD: postgres123
    ports:
      - "5432:5432"
  
  # 缓存服务
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  # API网关
  api-gateway:
    build: ./backend/api-gateway
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
  
  # 聊天服务
  chat-service:
    build: ./backend/chat-service
    ports:
      - "8001:8001"
```

### 🚀 用Docker Compose一键启动

在项目根目录执行：
```bash
docker-compose up -d
```

就这么简单！所有服务都启动了！🎉

---

## 5. 部署到服务器

### 🔧 部署前准备

#### 1. 准备一个云服务器
你可以从以下地方购买：
- 阿里云、腾讯云、华为云（国内）
- AWS、Google Cloud、Azure（国外）

#### 2. 安装必要的软件

在服务器上执行：
```bash
# 更新系统
sudo apt-get update

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo apt-get install docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 3. 配置环境变量

复制 `.env.example` 到 `.env`，填入真实配置：

```env
# PostgreSQL
POSTGRES_PASSWORD=your-strong-password-here

# OpenAI
OPENAI_API_KEY=your-openai-key-here

# 安全相关
SECRET_KEY=your-secret-key-here
```

### 📤 部署步骤

1. 上传代码到服务器（git clone或上传文件）
2. 在服务器上运行：
   ```bash
   cd backend-rag-customer-service
   docker-compose up -d
   ```
3. 配置域名和Nginx（生产环境需要）

### 🛡️ 安全设置（生产环境必备

- 修改默认密码
- 配置防火墙
- 启用HTTPS（SSL证书
- 定期备份数据
- 监控和日志

---

## 6. 调试与问题解决

### 🕵️ 查看服务日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f chat-service
docker-compose logs -f api-gateway
```

### 🔍 常见问题

#### 问题1：端口被占用
```bash
# 查找被占用的端口
sudo lsof -i :8000

# 杀掉进程或换一个端口
```

#### 问题2：服务无法启动
```bash
# 查看错误日志
docker-compose logs chat-service

# 尝试重启
docker-compose restart chat-service
```

#### 问题3：数据库连接失败
```bash
# 检查数据库服务是否运行
docker-compose ps

# 检查网络连接
docker-compose exec postgres ping
```

---

## 7. 总结与下一步

### 📚 整个课程回顾

我们一起学习了：
1. **Python基础** - 变量、函数、列表、字典
2. **Web开发** - FastAPI、路由、API
3. **数据库** - SQLite、SQLAlchemy、Redis、向量数据库
4. **微服务** - 项目架构、Docker、部署

### 🎯 你已经具备的能力

- 可以看懂和修改项目中的Python代码
- 理解Web框架和API
- 知道如何用数据库存储数据
- 理解微服务架构概念
- 会用Docker部署项目

### 🚀 下一步建议

1. **实际动手** - 运行项目，修改代码
2. **阅读源码** - 看每个服务的实现
3. **添加功能** - 尝试加一个小功能
4. **学习更多** - 深入学习各个技术细节
5. **贡献项目** - 参与开源项目

### 📖 项目中的学习路径

建议按以下顺序学习项目代码：
1. `backend/admin-console-api/` - 简单的管理API
2. `backend/chat-service/` - 核心聊天逻辑
3. `backend/knowledge-service/` - 知识库和向量
4. `frontend-*` - 前端代码（JavaScript

---

## 🎉 恭喜毕业！

你已经完成了完整的课程！从Python初学者到能够理解企业级项目的架构，很棒！

**继续探索，永远保持学习的热情！✨
