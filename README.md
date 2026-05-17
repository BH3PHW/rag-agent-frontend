# RAG Agent 前端

一个通用的 RAG (检索增强生成) Agent 前端应用，支持多用户、企业知识库管理和智能问答。

## 功能特性

- 👥 **多用户系统**: 用户注册登录、企业管理
- 📚 **企业知识库**: 为每个企业创建独立的知识库
- 🤖 **智能聊天**: 与 AI 对话，支持 Markdown 渲染和来源引用
- 📄 **文档管理**: 支持拖拽上传，多种文档格式
- 🧹 **数据清洗**: 文档预处理和清洗功能
- ⚙️ **灵活配置**: 可自定义 API 密钥、模型参数等
- 💾 **本地存储**: 数据自动保存到浏览器本地存储
- 🐳 **Docker 支持**: 一键部署
- 🔗 **后端集成**: 与 RAG 智能客服后端完美协同

## 快速开始

### 使用 Docker (推荐)

```bash
# 方式一：仅前端
docker-compose up -d --build

# 方式二：前后端完整部署
docker-compose -f docker-compose.integrated.yml up -d --build

# 访问 http://localhost:3000
```

### 本地开发

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build
```

## 项目结构

```
rag-agent-frontend/
├── src/
│   ├── api/              # API 客户端（集成后端）
│   ├── pages/            # 页面组件
│   │   ├── Chat.tsx      # 聊天页面
│   │   ├── Documents.tsx  # 文档管理
│   │   ├── Users.tsx     # 用户管理
│   │   ├── Cleaning.tsx  # 数据清洗
│   │   └── Settings.tsx  # 设置页面
│   ├── types.ts          # TypeScript 类型定义
│   ├── store.ts          # Zustand 状态管理
│   ├── App.tsx           # 主应用组件
│   └── main.tsx          # 入口文件
├── Dockerfile            # Docker 配置
├── docker-compose.yml    # 独立前端部署
├── docker-compose.integrated.yml  # 前后端完整部署
└── nginx.conf           # Nginx 配置
```

## 与后端集成

本前端需要配合后端服务使用：

### 后端项目
🔗 **https://github.com/BH3PHW/rag-customer-service**

### 前后端部署

```bash
# 1. 克隆后端项目
git clone https://github.com/BH3PHW/rag-customer-service.git

# 2. 配置环境变量
cd rag-customer-service
cp .env.example .env
# 编辑 .env，添加阿里云百炼 API Key
# QWEN_API_KEY=your_api_key_here

# 3. 启动所有服务
docker-compose -f docker-compose.integrated.yml up -d --build

# 4. 访问应用
# 前端: http://localhost:3000
# API:  http://localhost:8000
```

## 技术栈

- **前端框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **图标**: Lucide React
- **Markdown**: React Markdown
- **HTTP 客户端**: Fetch API

## 使用流程

1. **访问前端**: 打开 http://localhost:3000
2. **注册账号**: 进入 Profile 页面注册新账号
3. **创建企业**: 注册后创建企业
4. **上传文档**: 进入 Documents 页面，上传知识库文档
5. **开始问答**: 进入 Chat 页面，开始 RAG 智能问答

## API 集成

前端通过以下端点与后端通信：

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/enterprises` - 创建企业
- `GET /api/v1/knowledge-bases` - 获取知识库列表
- `POST /api/v1/knowledge-bases/{id}/documents` - 上传文档
- `POST /api/v1/chat/sessions` - 创建会话
- `POST /api/v1/chat/sessions/{id}/messages` - 发送消息

## License

本项目采用 **GNU General Public License v3.0 (GPL-3.0)** 开源许可证。

这意味着：
- ✅ 您可以自由使用、修改和分发本软件
- ✅ 修改后的版本必须以相同的 GPL-3.0 许可证开源
- ✅ 引用或基于本项目的衍生项目也必须开源

详情请参阅：[LICENSE](LICENSE) 文件

Copyright (C) 2026 RAG Customer Service
