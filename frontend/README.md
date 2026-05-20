# RAG智能客服系统 - 前端应用

## 项目简介

RAG智能客服系统前端应用，包含三个独立的前端项目，采用React+TypeScript+Vite技术栈。支持消费者端、企业管理端、系统管理端三个用户角色。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **状态管理**: Zustand (轻量级)
- **UI组件**: 自定义组件
- **包管理**: npm workspaces

## 应用结构

```
frontend/
├── apps/
│   ├── consumer/          # 消费者端 (3001)
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── api/client.ts
│   │   │   └── pages/Chat.tsx
│   │   └── package.json
│   ├── enterprise/        # 企业管理端 (3002)
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── api/client.ts
│   │   │   └── pages/
│   │   └── package.json
│   ├── agent-portal/      # 客服坐席门户 (3004)
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── api/client.ts
│   │   │   ├── store.ts
│   │   │   ├── types.ts
│   │   │   └── pages/
│   │   └── package.json
│   └── system-admin-portal/ # 系统管理端 (3003)
│       ├── src/
│       │   ├── App.tsx
│       │   ├── auth/
│       │   └── pages/
│       └── package.json
├── packages/
│   ├── ui/        # 共享UI组件
│   ├── store/     # 共享状态管理
│   └── api-client/ # 统一API客户端
├── tests/              # 测试脚本
└── package.json
```

## 快速开始

### 环境要求

- Node.js 18+
- npm 9+

### 安装依赖

```bash
# 安装所有应用的依赖
npm install
```

### 启动开发服务器

```bash
# 消费者端 (3001)
cd apps/consumer
npm run dev

# （另一个终端）企业端 (3002)
cd apps/enterprise
npm run dev

# （另一个终端）客服坐席门户 (3004)
cd apps/agent-portal
npm run dev

# （另一个终端）系统管理端 (3003)
cd apps/system-admin-portal
npm run dev
```

## 各应用功能

### 消费者端 (Consumer)
- 🎨 浮动客服聊天窗口
- 💬 实时智能对话
- ⚡ SSE流式输出 (打字机效果)
- 📱 响应式设计，支持移动端

访问地址: http://localhost:3001

### 企业管理端 (Enterprise)
- 📊 会话监控与管理
- 📚 知识库管理（文档上传、编辑）
- 🔌 渠道接入管理
- 🛡️ 敏感词与安全设置
- 👥 团队成员管理
- 📈 数据统计与分析

访问地址: http://localhost:3002

### 客服坐席门户 (Agent Portal)
- 🔐 坐席登录认证（OAuth2）
- 📊 坐席仪表盘（会话统计、在线状态）
- 📋 等待接入会话列表（支持优先级）
- 💬 我的会话管理
- 💭 实时对话（发送消息、结束会话）
- 🔄 WebSocket实时通知

访问地址: http://localhost:3004

测试账号：
- 用户名：agent1 / agent2
- 密码：123456

### 系统管理端 (System Admin Portal)
- 🏢 企业租户管理
- 👤 用户管理
- ⚙️ 系统配置
- 📊 数据分析
- 🔔 告警管理
- 📈 服务监控

访问地址: http://localhost:3003

## 生产构建

```bash
# 构建所有应用
npm run build

# 或构建单个应用
npm run build --workspace=apps/consumer
npm run build --workspace=apps/enterprise
npm run build --workspace=apps/agent-portal
npm run build --workspace=apps/system-admin-portal
```

## 环境变量配置

各应用使用 VITE_ 前缀的环境变量：

```env
# API Gateway 地址
VITE_API_BASE_URL=http://localhost:8080

# 应用环境
VITE_APP_ENV=development
```

## 开发指南

### 添加新页面

1. 在 `apps/[app-name]/src/pages/` 目录创建新的React组件
2. 在 `App.tsx` 中添加路由和菜单
3. 在 `api/client.ts` 中添加相应的API调用函数（或使用 @rag/api-client 包）

### 调试技巧

- 打开浏览器开发者工具 (F12)
- 查看 Console 中的 API 请求和响应
- 使用 Network 标签查看请求详情
- 检查是否有 CORS 错误或 API 地址错误

## 文档与资源

- [系统管理端使用指南](./apps/system-admin-portal/README.md)
- [前端测试指南](./tests/README.md)

## 许可证

MIT License
