# RAG 智能客服系统 - 前端架构

## 📦 项目结构

本项目采用 **Monorepo** 架构，使用 npm workspaces 管理多个独立应用和共享包。

```
frontend/
├── apps/                          # 应用层
│   ├── consumer/                 # 用户端 Widget (React + TypeScript)
│   ├── enterprise/              # 企业管理控制台 (React + TypeScript)
│   └── system-admin/            # 系统管理后台 (React + TypeScript)
│
├── packages/                     # 共享包层
│   ├── ui/                      # 共享 UI 组件库
│   └── store/                   # 共享状态管理库
│
├── package.json                 # Monorepo 根配置
├── tailwind.config.js          # 共享 Tailwind 配置
└── postcss.config.js           # 共享 PostCSS 配置
```

## 🚀 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 运行开发服务器

#### 运行单个应用

```bash
# 用户端 Widget (端口 3003)
npm run dev:consumer

# 企业管理控制台 (端口 3001)
npm run dev:enterprise

# 系统管理后台 (端口 3002)
npm run dev:system-admin
```

#### 同时运行所有应用

```bash
npm run dev
```

### 构建生产版本

```bash
# 构建所有应用
npm run build

# 构建单个应用
npm run build:consumer
npm run build:enterprise
npm run build:system-admin
```

## 📱 应用说明

### 1. 用户端 Widget (consumer)

面向终端用户的智能客服 Widget，包含：
- 💬 智能对话（RAG 增强）
- 🔄 实时流式响应
- 📎 消息输入与发送

**技术栈**：React 18 + TypeScript + Tailwind CSS + Zustand

**端口**：3003

---

### 2. 企业管理控制台 (enterprise)

面向企业的客服管理平台，包含：
- 📚 知识库管理
- 📄 文档上传与管理
- 🧹 数据清洗
- 🛡️ 敏感词设置
- 💬 对话监控
- 👨‍💻 人工坐席管理
- 🔗 渠道接入配置
- ⚙️ 系统设置

**技术栈**：React 18 + TypeScript + Tailwind CSS

**端口**：3001

---

### 3. 系统管理后台 (system-admin)

系统管理员专用后台，包含：
- 🏢 租户管理
- 👥 用户管理
- 🤖 大模型配置
- 💾 存储配置
- 📊 服务监控
- 🔔 告警中心
- ⚙️ API/模型参数设置

**技术栈**：React 18 + TypeScript + Tailwind CSS

**端口**：3002

---

## 🎨 共享组件库 (@rag/ui)

提供统一的 UI 组件，包含：

- **Button** - 多样式按钮组件
- **Card** - 卡片容器组件
- **Input** / **Textarea** - 表单输入组件
- **Tabs** - 标签页组件
- **NavItem** - 导航项组件
- **Layout** - 页面布局组件
- **LoadingSpinner** - 加载动画
- **Tag** - 标签组件

### 使用示例

```tsx
import { Button, Card, Input } from '@rag/ui';

function Example() {
  return (
    <Card>
      <Input label="用户名" placeholder="请输入" />
      <Button>提交</Button>
    </Card>
  );
}
```

---

## 🏪 共享状态管理 (@rag/store)

提供全局状态管理，包含：

- **useAuthStore** - 用户认证状态
- **useChatStore** - 聊天会话状态
- **apiClient** - API 请求封装

### 使用示例

```tsx
import { useAuthStore, apiClient } from '@rag/store';

// 获取用户信息
const { user, login } = useAuthStore();

// 发送 API 请求
const data = await apiClient('/users/me');
```

---

## 🎯 开发规范

### 命名规范

- 组件文件：`PascalCase.tsx` (如 `KnowledgeBase.tsx`)
- 工具函数：`camelCase.ts` (如 `apiClient.ts`)
- 常量：`UPPER_SNAKE_CASE` (如 `MAX_RETRIES`)

### 目录结构

```
apps/{app-name}/
├── src/
│   ├── pages/           # 页面组件
│   ├── components/      # 业务组件
│   ├── hooks/          # 自定义 Hooks
│   ├── api/            # API 客户端
│   ├── utils/         # 工具函数
│   ├── store.ts       # 状态管理
│   ├── types.ts       # 类型定义
│   ├── App.tsx        # 应用入口
│   └── main.tsx       # 渲染入口
├── package.json
├── vite.config.ts
├── tsconfig.json
└── index.html
```

### 代码风格

- 使用 **TypeScript** 严格模式
- 组件使用 **函数式组件**
- 状态管理使用 **Zustand**
- 样式使用 **Tailwind CSS**
- 图标使用 **Lucide React**

---

## 🔧 技术栈

### 核心框架
- React 18.3
- TypeScript 5.8
- Vite 6.3

### UI 框架
- Tailwind CSS 3.4
- Lucide React (图标库)
- PostCSS + Autoprefixer

### 状态管理
- Zustand 5.0

### 开发工具
- ESLint
- TypeScript
- Vite

---

## 📦 Docker 部署

每个应用都可以独立 Docker 化：

```bash
# 构建 Docker 镜像
docker build -t rag-consumer ./apps/consumer
docker build -t rag-enterprise ./apps/enterprise
docker build -t rag-system-admin ./apps/system-admin
```

或者使用 docker-compose：

```bash
docker-compose -f docker-compose.integrated.yml up
```

---

## 🚀 性能优化

### 代码分割
- 每个应用独立构建
- 使用 React.lazy 进行路由分割
- 共享包单独构建

### 优化策略
- Tailwind CSS 生产构建使用 purge
- Vite 生产构建使用 minify
- 图片资源优化
- 懒加载组件

---

## 📝 许可

本项目采用 GNU General Public License v3.0 开源许可。
