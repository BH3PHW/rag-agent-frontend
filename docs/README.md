# 🎉 RAG 智能客服系统 - 完整项目

## 📋 项目概述

这是一个完整的 RAG 智能客服系统，包含四个独立部分：

1. **消费者前端** - 用户端客服 Widget
2. **企业前端** - 企业管理控制台
3. **系统管理员前端** - 平台系统管理
4. **服务后端** - 微服务架构后端

---

## 🚀 快速启动

### 1. 启动后端服务
```bash
cd backend
docker-compose up
```

### 2. 启动消费者前端（用户端）
```bash
cd frontend-consumer
python3 -m http.server 3000 --directory public
```
访问：http://localhost:3000

### 3. 启动企业前端（管理端）
```bash
cd frontend-enterprise
python3 -m http.server 8080 --directory public
```
访问：http://localhost:8080

### 4. 启动系统管理员前端
```bash
cd frontend-system-admin
python3 -m http.server 9090 --directory public
```
访问：http://localhost:9090

---

## 📁 完整项目结构

```
backend-rag-customer-service/
│
├── frontend-consumer/              # 1. 消费者前端
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   └── rag-customer-service-widget-v2.js
│   ├── package.json
│   └── README.md
│
├── frontend-enterprise/            # 2. 企业前端
│   ├── public/
│   │   ├── index.html
│   │   ├── guide.html
│   │   └── js/
│   │       └── app.js
│   ├── package.json
│   └── README.md
│
├── frontend-system-admin/          # 3. 系统管理员前端
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── README.md
│
├── backend/                        # 4. 服务后端
│   ├── api-gateway/
│   ├── chat-service/
│   ├── channel-service/
│   ├── knowledge-service/
│   ├── user-service/
│   ├── analytics-service/
│   ├── alert-service/
│   ├── admin-console-api/
│   ├── common/
│   ├── docker-compose.yml
│   └── README.md
│
└── docs/                           # 项目文档
    ├── PROJECT_STRUCTURE.md
    └── (其他文档...)
```

---

## 🎯 各部分功能详解

### 1. 消费者前端 (frontend-consumer)
- **用户**: 终端消费者
- **功能**: 智能客服对话 Widget
- **特色**: 流式对话、打字机效果、多渠道适配
- **技术**: 原生 JavaScript（无依赖）

### 2. 企业前端 (frontend-enterprise)
- **用户**: 企业管理员/运营人员
- **功能**:
  - 📊 控制台概览
  - 📚 知识库管理
  - 🔌 渠道接入
  - 💬 对话监控
  - ❓ FAQ 管理
  - 📈 数据统计
  - 💰 计费中心
  - ⚙️ 系统设置
  - 👥 团队管理
  - 📋 系统日志
- **技术**: 原生 JavaScript（无依赖）

### 3. 系统管理员前端 (frontend-system-admin)
- **用户**: 平台系统管理员
- **功能**:
  - 📊 系统概览
  - 🏢 租户管理
  - 👤 用户管理
  - ⚙️ 服务监控
  - 💳 计费管理
  - 📋 系统日志
  - 🔧 系统设置
- **技术**: 原生 JavaScript（无依赖）

### 4. 服务后端 (backend)
- **架构**: 微服务架构
- **服务列表**:
  - API Gateway（统一入口）
  - Chat Service（聊天服务）
  - Channel Service（渠道接入）
  - Knowledge Service（知识库）
  - User Service（用户管理）
  - Analytics Service（数据分析）
  - Alert Service（告警通知）
  - Admin Console API（管理后台API）
- **技术栈**: FastAPI + Python

---

## 📊 端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 消费者前端 | 3000 | 用户端 Widget |
| 企业前端 | 8080 | 企业管理控制台 |
| 系统管理员前端 | 9090 | 平台管理控制台 |
| API Gateway | 8000 | 后端网关 |
| Admin Console API | 8080 | 企业管理API |
| (其他微服务...) | | |

---

## 🎨 设计特色

### 前后端完全分离
- 三个前端项目完全独立
- 通过 REST API 与后端通信
- 可独立部署和扩展

### 无外部依赖
- 前端全部使用原生 JavaScript
- 无框架依赖，加载速度快
- 易于维护和升级

### 微服务架构
- 后端服务模块化
- 可独立扩展和部署
- 高可用性设计

---

## 📚 更多文档

查看项目根目录下的文档文件了解更多详情！
