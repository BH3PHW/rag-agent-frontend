# RAG 智能客服 - Python 入门教程 2：Web开发入门

## 📚 目录
1. [什么是Web框架
2. [FastAPI入门
3. [写你的第一个API
4. [在项目中看真实的代码
5. [理解路由与请求
6. [总结与练习

---

## 1. 什么是Web框架？

### 🌐 网页访问原理

在开始之前，让我们先理解一下当你访问一个网站时发生了什么：

```
你 (浏览器) → 发送请求 → 服务器 → 返回回复 → 显示在浏览器
```

### 🎯 为什么需要Web框架？

想象一下，如果不使用框架，我们需要做哪些事：
- 监听网络端口
- 解析用户请求
- 处理各种错误
- 发送响应
- 处理网页资源

框架会帮我们完成这些复杂的事情！我们这个项目使用的是 **FastAPI**。

---

## 2. FastAPI入门

### 📦 安装FastAPI

首先，我们需要安装必要的包。在命令行输入：
```bash
pip install fastapi
pip install uvicorn
```

### 🏗️ 你的第一个FastAPI程序

创建一个 `first_api.py` 文件：

```python
# 导入FastAPI
from fastapi import FastAPI

# 创建一个应用实例
app = FastAPI()

# 定义一个路由（当访问首页时
@app.get("/")
async def root():
    """根路径，显示欢迎信息"""
    return {
        "message": "你好，欢迎来到RAG智能客服！",
        "version": "1.0.0"
    }

# 另一个路由，处理问候
@app.get("/greet/{name}")
async def greet(name: str):
    """问候API，带名字参数"""
    return {
        "greeting": f"你好，{name}！",
        "message": "欢迎使用我们的服务"
    }

# 聊天API（简化版
@app.post("/chat/{user_id}")
async def chat(user_id: str, message: str):
    """简单的聊天API"""
    # 模拟回复
    responses = {
        "你好": "你好！我是智能客服",
        "帮助": "我可以帮你解答问题",
        "再见": "再见，有问题再来！"
    }
    
    response = responses.get(message, "抱歉，我不太明白")
    
    return {
        "user_id": user_id,
        "request": message,
        "response": response
    }

# 运行这个程序：
# uvicorn first_api:app --reload --port 8080
```

### 运行你的API

在命令行中运行：
```bash
uvicorn first_api:app --reload --port 8080
```

现在访问：
- 浏览器打开 `http://localhost:8080`  - 看到欢迎信息
- 访问 `http://localhost:8080/docs`  - Swagger文档（这是测试API的好工具！）

---

## 3. 看项目中的真实代码

现在让我们看一下真实项目中的代码：
`backend/admin-console-api/main.py`

```python
from fastapi import FastAPI

# 创建应用
app = FastAPI(
    title="RAG 智能客服 - 管理后台 API",
    description="完整的系统管理功能",
    version="2.2.0"
)

# 健康检查
@app.get("/")
async def root():
    return {
        "name": "RAG 智能客服 - 管理后台 API",
        "version": "2.2.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "admin-console-api"
    }

@app.get("/api/v1/dashboard/summary")
async def dashboard_summary():
    """返回仪表盘数据"""
    return {
        "success": True,
        "data": {
            "total_tenants": 127,
            "active_users": 8432,
            "total_chats": 245678,
            "satisfaction_rate": 98.5
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## 4. 理解路由与请求

### 🛣️ HTTP方法

常见的HTTP方法：
- `GET` - 获取数据（查询）
- `POST` - 创建数据（发送内容）
- `PUT` - 更新数据
- `DELETE` - 删除数据

### 🍪 让我们创建一个聊天服务器（简化版）

创建 `simple_chat_server.py`：

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="简化聊天服务")

# 数据模型（Pydantic
class ChatMessage(BaseModel):
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: str

class ChatSession:
    def __init__(self):
        self.messages: List[ChatMessage] = []

# 会话存储（简单字典
sessions = {}

# 创建会话
@app.post("/api/sessions/{user_id}")
async def create_session(user_id: str):
    """创建新会话"""
    session_id = f"session_{user_id}"
    sessions[session_id] = ChatSession()
    
    return {
        "success": True,
        "session_id": session_id,
        "message": "会话创建成功"
    }

# 发送消息
@app.post("/api/sessions/{session_id}/messages")
async def send_message(session_id: str, message: str):
    """发送消息到会话"""
    if session_id not in sessions:
        return {
            "success": False,
            "error": "会话不存在"
        }
    
    # 保存用户消息
    from datetime import datetime
    user_msg = ChatMessage(
        role="user",
        content=message,
        timestamp=datetime.now().strftime("%H:%M:%S")
    )
    sessions[session_id].messages.append(user_msg)
    
    # 模拟AI回复
    ai_response = {
        "你好": "你好！我是智能客服",
        "帮助": "我可以帮你解答问题",
        "再见": "再见，有问题再来！"
    }.get(message, "抱歉，我不太明白")
    
    ai_msg = ChatMessage(
        role="assistant",
        content=ai_response,
        timestamp=datetime.now().strftime("%H:%M:%S")
    )
    sessions[session_id].messages.append(ai_msg)
    
    return {
        "success": True,
        "message": ai_response
    }

# 获取聊天历史
@app.get("/api/sessions/{session_id}/history")
async def get_history(session_id: str):
    """获取会话历史"""
    if session_id not in sessions:
        return {
            "success": False,
            "error": "会话不存在"
        }
    
    return {
        "success": True,
        "messages": sessions[session_id].messages
    }

if __name__ == "__main__":
    import uvicorn
    print("🎉 简化聊天服务启动在 http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## 5. 理解数据模型（Pydantic）

在项目中，我们使用 `Pydantic` 来管理数据结构。这非常重要！

创建一个 `models_example.py`：

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# 枚举类型（有限的选择
class UserRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    GUEST = "guest"

# 用户数据模型
class User(BaseModel):
    user_id: str = Field(..., description="用户ID")
    name: str = Field(..., description="用户姓名")
    email: Optional[str] = Field(None, description="可选邮箱")
    role: UserRole = UserRole.GUEST
    active: bool = True

    # 简单的验证
    def is_admin(self):
        return self.role == UserRole.ADMIN

# 使用示例
if __name__ == "__main__":
    # 创建用户
    user = User(
        user_id="user_001",
        name="张三",
        email="zhangsan@example.com",
        role=UserRole.ADMIN
    )
    
    print("用户信息:")
    print(f"  ID: {user.user_id}")
    print(f"  姓名: {user.name}")
    print(f"  邮箱: {user.email}")
    print(f"  角色: {user.role}")
    print(f"  是否管理员: {user.is_admin()}")

    # 序列化为JSON
    user_json = user.model_dump_json(indent=2)
    print("\nJSON格式:")
    print(user_json)
```

---

## 6. CORS跨域（浏览器与API通信

在 `backend/admin-console-api/main.py` 中有CORS设置：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产时要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 为什么需要CORS？

浏览器有安全限制，不能随便访问不同域名的API。CORS配置告诉浏览器，哪些请求是被允许的。

---

## 7. 总结与练习

### 📝 这节课你学到了什么？
- 什么是Web框架
- FastAPI的基本使用
- 路由和请求处理
- Pydantic数据模型
- CORS配置
- API文档的使用

### 🎯 练习任务：

1. 写一个简单的FAQ问答API
2. 支持查询和添加FAQ
3. 使用Pydantic定义FAQ数据模型
4. 测试你的API（访问 /docs）

### 💡 提示：

FAQ数据结构示例：
```python
class FAQ(BaseModel):
    question: str
    answer: str
    category: str
    views: int = 0
```

---

**继续前进！下节课我们学习数据库！🎉
