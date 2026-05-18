# RAG智能客服系统

## 项目简介

RAG智能客服系统是一个基于检索增强生成（RAG）技术的智能客服解决方案，采用微服务架构，支持多租户管理。

## 技术栈

### 前端
- React 18 + TypeScript
- Tailwind CSS
- Zustand (状态管理)
- Vite (构建工具)
- Monorepo 架构

### 后端
- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- ChromaDB (向量数据库)

## 项目结构

```
workspace/
├── backend/              # 后端微服务
│   ├── api-gateway/    # API网关
│   ├── user-service/    # 用户服务
│   ├── chat-service/    # 聊天服务
│   ├── knowledge-service/  # 知识库服务
│   ├── alert-service/   # 告警服务
│   └── channel-service/ # 渠道服务
├── frontend/            # 前端应用
│   ├── apps/
│   │   ├── consumer/   # 消费者端
│   │   ├── enterprise/ # 企业端
│   │   └── system-admin/ # 系统管理端
│   └── packages/
│       ├── ui/        # 共享UI组件
│       └── store/     # 共享状态
├── docs/               # 文档
├── tests/              # 测试脚本
└── docker-compose.yml  # Docker编排
```

## 快速开始

### 环境要求
- Node.js 18+
- Python 3.10+
- Docker & Docker Compose
- PostgreSQL
- Redis

### 启动服务

```bash
# 复制环境变量配置
cp .env.example .env

# 启动所有服务
docker-compose up -d

# 或手动启动后端
cd backend
pip install -r requirements.txt
uvicorn api-gateway.main:app --reload

# 启动前端
cd frontend
npm install
npm run dev
```

## 主要功能

- 🤖 智能问答：基于RAG技术的AI对话
- 📚 知识库管理：文档上传、检索
- 🔒 安全防护：防提示词注入、敏感词过滤
- 💬 多渠道接入：Web、微信公众号、钉钉等
- 👥 多租户管理：企业级隔离
- 📊 数据分析：对话统计、运营报表

## API文档

启动服务后访问：`http://localhost:8000/docs`

## 开发指南

### 前端开发
```bash
cd frontend
npm install
npm run dev        # 开发模式
npm run build      # 生产构建
npm run lint       # 代码检查
```

### 后端开发
```bash
cd backend
pip install -r requirements.txt

# 启动各个服务
uvicorn api-gateway.main:app --port 8000
uvicorn user-service.main:app --port 8001
uvicorn chat-service.main:app --port 8002
```

## 安全特性

- ✅ 防提示词注入（Prompt Injection Defense）
- ✅ SQL注入防护（SQLAlchemy ORM）
- ✅ API限流（Redis）
- ✅ CORS跨域保护
- ✅ JWT认证
- ✅ bcrypt密码加密
- ✅ 敏感词检测

## 测试

```bash
# 运行前端测试
cd frontend
npm test

# 运行后端测试
cd backend/tests
python3 debug_services.py all
```

## 文档

- [产品经理视角文档](./docs/产品经理视角-项目整合说明文档.md)
- [API规范文档](./tests/api-specification.md)
- [部署指南](./docs/DEPLOYMENT_GUIDE.md)
- [安全检查报告](./tests/security-check-report.md)

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
