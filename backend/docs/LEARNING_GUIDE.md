# 📚 RAG智能客服项目 - Python初学者完整教程

欢迎来到这个完整的Python入门教程！这个教程基于真实的企业级RAG（检索增强生成）智能客服项目，专为只了解Python基础语法的初学者设计。

---

## 🎯 教程概览

| 课程 | 主题 | 难度 | 时间 |
|------|------|------|------|
| 第1课 | [Python基础与项目入门](../learning/01_python_basics.md) | ⭐ | 1-2小时 |
| 第2课 | [Web开发与FastAPI](../learning/02_web_development.md) | ⭐⭐ | 2-3小时 |
| 第3课 | [数据库与持久化](../learning/03_database.md) | ⭐⭐ | 2-3小时 |
| 第4课 | [微服务架构与部署](../learning/04_microservices_deployment.md) | ⭐⭐⭐ | 2-3小时 |

---

## 📁 项目结构

```
/workspace/
├── backend/                         # 后端微服务
│   ├── api-gateway/                # API网关
│   ├── user-service/               # 用户服务
│   ├── chat-service/               # 聊天服务
│   ├── knowledge-service/          # 知识库服务
│   └── ...                         # 其他后端服务
├── frontend/                        # 前端项目
│   ├── agent/                      # React智能助手前端
│   ├── enterprise/                 # 企业管理前端
│   └── ...                         # 其他前端项目
├── docs/                           # 项目文档
│   ├── LEARNING_GUIDE.md           # 本文件
│   └── ...                         # 其他文档
├── learning/                       # 学习资源
│   ├── 01_python_basics.md         # 第1课
│   ├── 02_web_development.md       # 第2课
│   ├── 03_database.md              # 第3课
│   ├── 04_microservices_deployment.md  # 第4课
│   ├── COURSE_OVERVIEW.md          # 课程总览
│   └── PRACTICE/                   # 练习代码
└── docker-compose.yml              # Docker配置
```

---

## 🚀 开始学习

### 前置条件

- Python 3.10 或更高版本
- 基础的Python语法知识
- 对Web开发有基本了解（可选）

### 学习路线

#### 方式一：按顺序学习（推荐初学者）
1. 阅读 [课程总览](../learning/COURSE_OVERVIEW.md)
2. 从第1课开始，按顺序学习
3. 完成每课的练习代码
4. 阅读项目中的真实代码
5. 动手修改和实验

#### 方式二：快速上手（有一定基础）
1. 先看 [课程总览](../learning/COURSE_OVERVIEW.md)
2. 快速扫过第1课
3. 重点学习第2-4课
4. 直接运行练习代码

---

## 💻 练习代码

所有练习代码位于：[`../learning/PRACTICE/`](../learning/PRACTICE/)

| 练习文件 | 说明 |
|----------|------|
| `practice_01_hello.py` | Hello World与基础语法 |
| `practice_02_functions.py` | 函数练习 |
| `practice_03_lists_dicts.py` | 列表与字典 |
| `practice_04_simple_chat.py` | 简单聊天程序 |
| `practice_05_first_api.py` | 第一个FastAPI |
| `practice_06_simple_chat_api.py` | 聊天API |
| `practice_07_sqlite.py` | SQLite数据库 |
| `practice_08_orm.py` | SQLAlchemy ORM |
| `practice_09_redis.py` | Redis缓存 |
| `practice_10_complete_faq.py` | 完整FAQ系统 |

### 运行练习

```bash
# 进入练习目录
cd /workspace/learning/PRACTICE/

# 运行第1个练习
python practice_01_hello.py

# 运行API练习（需要先安装依赖）
pip install fastapi uvicorn
python practice_05_first_api.py
```

---

## 🔧 环境准备

### 安装Python依赖

```bash
# 基础依赖
pip install fastapi uvicorn sqlalchemy

# 完整项目依赖
cd /workspace
pip install -r requirements.txt
```

### Docker环境（可选）

如果想运行完整项目：

```bash
# 安装Docker和Docker Compose
# 然后运行
cd /workspace
docker-compose up -d
```

---

## 📖 项目学习建议

### 1. 从简单到复杂

建议按以下顺序阅读项目代码：

1. **先看简单的API**：`backend/user-service/` 或 `backend/admin-service/`
2. **再看核心功能**：`backend/chat-service/`
3. **然后是知识库**：`backend/knowledge-service/`
4. **最后看架构**：`docker-compose.yml`

### 2. 动手实践

- 修改练习代码，观察变化
- 在项目中添加小功能
- 尝试理解并修改配置
- 运行和调试项目

### 3. 常见问题

**Q: 我完全是Python新手，可以学吗？**
A: 可以！教程从最基础开始讲解。

**Q: 练习代码运行出错怎么办？**
A: 先看错误信息，再检查代码，或者回到对应课程重新学习。

**Q: 如何运行完整项目？**
A: 参考第4课的部署教程。

---

## 🎓 学习检查点

### 完成第1课后你应该能：
- 写简单的Python脚本
- 理解变量、函数、列表、字典
- 看懂项目中的配置文件

### 完成第2课后你应该能：
- 创建简单的FastAPI应用
- 理解API路由
- 定义Pydantic数据模型
- 测试API

### 完成第3课后你应该能：
- 操作SQLite数据库
- 理解ORM概念
- 使用Redis缓存
- 理解向量数据库概念

### 完成第4课后你应该能：
- 理解微服务架构
- 使用Docker
- 用Docker Compose部署
- 基础的服务器知识

---

## 🔗 相关资源

- [Python官方文档](https://docs.python.org/zh-cn/3/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/zh/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Docker文档](https://docs.docker.com/)

---

## 💡 学习技巧

1. **多动手写** - 每个示例都要亲自运行
2. **阅读真实代码** - 对比教程和项目实现
3. **不怕出错** - 错误是最好的老师
4. **做笔记** - 记录重要的点和问题
5. **循序渐进** - 不要急于求成

---

## 🎉 开始你的学习之旅吧！

现在，让我们从 [课程总览](../learning/COURSE_OVERVIEW.md) 开始！

祝你学习愉快！✨
