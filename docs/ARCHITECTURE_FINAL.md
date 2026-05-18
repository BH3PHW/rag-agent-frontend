# RAG 智能客服系统 - 完整架构文档

## 🎉 项目重构完成！

已完成完全的项目重构，实现了三个完全独立的子项目！

---

## 📦 架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                             项目根目录                               │
├─────────────────────────────────────────────────────────────────────┤
│  backend/                    ← 后端服务（完全独立）                  │
│    └── admin-console-api/   ← 管理后端 API                          │
│                                                                      │
│  frontend-user/              ← 用户端 Widget（完全独立）             │
│    ├── src/                                                          │
│    └── public/                                                       │
│                                                                      │
│  frontend-admin/             ← 管理端控制台（完全独立）              │
│    └── public/                                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 三个完全独立的子项目

### 1️⃣ **后端 (backend/)**
- **技术栈**：Python 3.10+、FastAPI、Uvicorn
- **完全独立**：可以单独部署
- **无前端代码**：只提供 REST API
- **端口**：8080
- **API 文档**：http://localhost:8080/docs

### 2️⃣ **用户端 Widget (frontend-user/)**
- **技术栈**：原生 JavaScript（无任何依赖）、HTML5、CSS3
- **完全独立**：可以嵌入任何网站
- **零依赖**：无需任何构建工具或第三方库
- **特点**：支持 SSE 流式输出、打字机效果
- **端口**：3000

### 3️⃣ **管理端控制台 (frontend-admin/)**
- **技术栈**：原生 JavaScript（无任何依赖）、HTML5、CSS3
- **完全独立**：可以独立部署到 CDN
- **零依赖**：无需任何构建工具
- **特点**：知识库管理、渠道接入、对话监控、FAQ 管理
- **端口**：8080

---

## 🎯 技术栈一致性

### 后端技术栈（统一）
- FastAPI 框架
- Pydantic 数据验证
- Uvicorn 服务器
- 标准 REST API 规范

### 前端技术栈（统一）
- 原生 JavaScript（ES6+）
- HTML5、CSS3
- 零第三方依赖
- 通过 REST API 与后端通信

---

## 🚀 快速启动指南

### 启动后端
```bash
cd backend/admin-console-api
pip install -r requirements.txt
python main.py
```

### 启动用户端 Widget
```bash
cd frontend-user
python3 -m http.server 3000 --directory public
```
访问：http://localhost:3000

### 启动管理端控制台
```bash
cd frontend-admin
python3 -m http.server 8081 --directory public
```
访问：http://localhost:8081

---

## 🔗 通信方式

所有模块之间通过标准 REST API 通信：
- 前端 ↔ 后端：JSON 格式
- 完全无耦合
- 可独立扩展和替换

---

## ✨ 重构成果

| 检查项 | 状态 |
|-------|------|
| 后端完全独立 | ✅ |
| 用户前端完全独立 | ✅ |
| 管理前端完全独立 | ✅ |
| 技术栈一致 | ✅ |
| 无依赖混用 | ✅ |
| 模块间完全解耦 | ✅ |
| 零第三方依赖（前端） | ✅ |

---

## 📖 详细文档

每个项目都有独立的 README.md 文档：
- [backend/README.md](backend/README.md)
- [frontend-user/README.md](frontend-user/README.md)
- [frontend-admin/README.md](frontend-admin/README.md)
