# RAG 智能客服 - Python 入门教程总览

## 📚 课程目录

欢迎来到完整的Python入门教程！这个系列以我们的RAG智能客服项目为基础，从Python基础到企业级架构。

---

## 📖 课程列表

### 1. Python基础入门
[01_python_basics.md](01_python_basics.md)
- Python安装与环境配置
- 变量、数据类型
- 函数、列表、字典
- 项目结构概览

### 2. Web开发入门
[02_web_development.md](02_web_development.md)
- FastAPI框架
- 路由与API
- 数据模型
- CORS配置

### 3. 数据库与持久化
[03_database.md](03_database.md)
- SQLite入门
- SQLAlchemy ORM
- Redis缓存
- ChromaDB向量数据库

### 4. 微服务架构与部署
[04_microservices_deployment.md](04_microservices_deployment.md)
- 微服务架构概念
- Docker与容器化
- Docker Compose
- 服务器部署

---

## 🗂️ 项目结构快速导航

```
LEARNING/
├── 01_python_basics.md              # 第1课
├── 02_web_development.md            # 第2课
├── 03_database.md                   # 第3课
├── 04_microservices_deployment.md   # 第4课
├── COURSE_OVERVIEW.md               # 本文件
└── PRACTICE/                        # 练习代码（见下一节
```

---

## 🎯 学习路线建议

### 初学者路径（从0开始）
1. **第1周** - Python基础（01_python_basics.md）
   - 完成所有练习
   - 能看懂简单的Python代码

2. **第2周** - Web开发（02_web_development.md）
   - 运行FastAPI示例
   - 写你的第一个API
   - 看项目中的管理API代码

3. **第3周** - 数据库（03_database.md）
   - 练习SQLite
   - 理解ORM概念
   - 看项目的数据库模型

4. **第4周** - 架构与部署（04_microservices_deployment.md）
   - 理解整体架构
   - 运行Docker示例
   - 尝试部署到服务器

### 有Python基础者
1. 快速扫一遍第1课
2. 重点学习第2-4课
3. 直接看项目代码和练习

---

## 🚀 如何开始学习？

### 第1步：准备环境
```bash
# 确保你有Python 3.10+
python --version

# 安装必要的包
pip install fastapi uvicorn sqlalchemy redis chromadb
```

### 第2步：按顺序学习
1. 从 `01_python_basics.md` 开始
2. 完成课程中的练习
3. 看项目中的真实代码
4. 动手运行和修改

### 第3步：循序渐进
不要急！先理解基础，再看复杂的代码。

---

## 💡 学习技巧

### 1. 多动手写
- 每个示例代码都要亲自运行
- 修改参数，看结果变化
- 尝试自己写类似的功能

### 2. 阅读真实项目代码
- 边看教学文档，边看项目中的实现
- 对比教学示例和项目代码
- 理解为什么项目那样实现

### 3. 不怕出错
- 错误是最好的老师
- 遇到Bug，先自己尝试解决
- 查资料、问朋友

### 4. 做笔记
- 记录你觉得重要的点
- 记录遇到的问题和解决方案
- 定期回顾

---

## 🎓 学习检查点

### 第1课学完你应该能够：
- ✅ 写简单的Python脚本
- ✅ 理解变量、函数、列表、字典
- ✅ 看懂项目中的配置文件

### 第2课学完你应该能够：
- ✅ 创建简单的FastAPI应用
- ✅ 理解API路由
- ✅ 定义Pydantic数据模型
- ✅ 测试API

### 第3课学完你应该能够：
- ✅ 操作SQLite数据库
- ✅ 理解ORM概念
- ✅ 使用Redis缓存
- ✅ 理解向量数据库概念

### 第4课学完你应该能够：
- ✅ 理解微服务架构
- ✅ 使用Docker
- ✅ 用Docker Compose部署
- ✅ 基础的服务器知识

---

## 📋 学习资源

### 项目文件建议阅读顺序
1. `backend/user-service/main.py` - 简单易懂的用户服务API
2. `backend/chat-service/main.py` - 核心业务逻辑
3. `backend/knowledge-service/main.py` - 知识库服务
4. `frontend/enterprise/public/js/app.js` - 前端交互逻辑
5. `docker-compose.yml` - 整体架构

### 官方文档
- Python: https://docs.python.org/zh-cn/3/
- FastAPI: https://fastapi.tiangolo.com/zh/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Docker: https://docs.docker.com/

---

## 🎉 开始你的学习之旅吧！

选择一个课程开始，记住，最好的学习方式是动手实践！

有问题？别担心，继续前进，问题会慢慢解决的。加油！✨

---

**下一站：[01_python_basics.md](01_python_basics.md) - Python基础入门！**
