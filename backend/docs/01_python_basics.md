# RAG 智能客服 - Python 入门教程 1：从零开始

## 📚 目录
1. [欢迎来到Python与项目介绍
2. [准备工作
3. [项目结构概览
4. [你的第一个Python程序
5. [从项目中的Python基础
6. [总结与下一步

---

## 1. 欢迎来到Python与项目介绍

### 👋 你好，欢迎！

恭喜你开始学习这个完整的企业级项目！这个RAG（检索增强生成）智能客服系统！

### 💡 什么是这个项目？
这是一个完整的智能客服系统，它可以：
- 自动回答客户问题
- 理解用户意图
- 知识库问答
- 支持网页和微信等多渠道
- 支持大模型配置
- 支持流式对话（打字机效果）
- 敏感问题转接人工客服

### 🎯 你将学到什么？

通过学习这个项目，你将学会：
- Python基础概念
- Web服务器开发
- 数据库操作
- API（检索增强生成）概念
- 实际的Web开发技术

---

## 2. 准备工作

### ✅ 安装Python

如果你还没有安装Python，请按照以下步骤操作：

#### 在Windows上：
1. 访问 https://www.python.org/downloads/
2. 下载最新版本的Python（建议 3.10 或更高）
3. 运行安装程序，记得勾选「Add Python to PATH」
4. 打开命令行（CMD），输入：
   ```bash
   python --version
   ```
   如果显示版本号，说明安装成功！

#### 在Mac/Linux上：
```bash
python3 --version
```

### 📦 安装必要的工具

你需要学习的工具：
- **VS Code（推荐）或者其他你喜欢的编辑器
- 学习时的基础知识

### 💻 认识一下我们的项目

让我们先看看项目的结构（只看关键部分：

```
backend-rag-customer-service/
├── backend/
│   ├── chat-service/      # 聊天服务
│   ├── knowledge-service/ # 知识库服务
│   └── ...其他服务
├── frontend-consumer/      # 消费者前端
├── frontend-enterprise/  # 企业前端
└── docs/                  # 文档
```

---

## 3. 项目结构概览（Python后端部分）

### 🎯 微服务架构

虽然这听起来很重要，但我们先从简单的开始！

让我们先认识一些常见的项目文件：

### 文件类型说明：
- `.py` - Python源文件，你写的代码就在这里面
- `Dockerfile` - 配置文件，用于部署
- `requirements.txt` - 告诉Python依赖库

让我们先看看一个最简单的Python文件

---

## 4. 你的第一个Python程序

### 🏃 写一个简单的Python程序

在你的项目目录中创建一个新文件，叫 `hello.py`：

```python
# 这是一个注释，Python不会执行注释
print("你好，世界！")
print("欢迎来到RAG智能客服项目！")

# 定义变量
name = "小明"
age = 25

print(f"我叫{name}，今年{age}岁")

# 简单的数学运算
a = 10
b = 20
print(f"{a} + {b} = {a + b}")

# 条件语句
if age > 18:
    print("你是成年人了")
else:
    print("你还没成年呢")

# 循环
for i in range(5):
    print(f"第{i}次：你好")
```

### 运行你的程序

在命令行输入：
```bash
python hello.py
```

恭喜你！你写了第一个Python程序！🎉

---

## 5. 从项目中的Python基础

现在让我们看一下项目中真实的Python代码，先看一个简单的例子。

### 看一下项目中的配置文件

我们先看一个最简单的配置文件：

`backend/chat-service/config.py`（为了简单，我们简化一下内容：

```python
# 配置文件 - 这是一个常见的Python文件

# 定义一些常量
DEFAULT_ENTERPRISE_ID = "demo-enterprise"
DEFAULT_USER_ID = "demo-user"

# 配置API端点
API_GATEWAY_URL = "http://localhost:8000"

# 输出这些配置
print("配置加载中...")
print(f"企业ID: {DEFAULT_ENTERPRISE_ID}")
print(f"API地址: {API_GATEWAY_URL}")

print("配置加载完成！")
```

### 理解函数（Function）

函数是一段重复使用的代码块。我们先看项目中的函数：

```python
# 简单函数示例
def greet(name):
    """一个简单的问候函数"""
    return f"你好，{name}！"

# 使用函数
message = greet("小明")
print(message)

# 另一个函数，带两个参数
def add(a, b):
    """加法函数"""
    return a + b

result = add(5, 3)
print(f"结果: {result}")
```

### 列表（List）

列表是项目中经常使用的数据结构：

```python
# 创建一个列表
faq_list = [
    "如何退货？",
    "配送时间？",
    "客服电话？"
]

# 遍历列表
for faq in faq_list:
    print(f"- {faq}")

# 添加新问题
faq_list.append("新的问题")
```

### 字典（Dictionary）

字典是存储键值对的数据结构：

```python
# 示例字典
faq_answers = {
    "如何退货？": "请在订单页面申请退货",
    "配送时间？": "通常24小时内发货"
}

# 查询字典
question = "如何退货？"
answer = faq_answers.get(question, "抱歉，我不太清楚")
print(f"问: {question}")
print(f"答: {answer}")
```

---

## 6. 让我们理解项目中最基础的服务

### 创建一个最简单的Web服务器

让我们看一个很简单的，类似项目中的web服务的简化版本。

创建一个 `simple_server.py` 文件：

```python
# 这是一个简单的服务器示例
# 注意：这是一个简化版本，不是项目真实代码

print("🎉 简单服务器启动中...")
print("👉 访问 http://localhost:8000 来测试")

# 模拟路由（简单字典存储
chat_history = []

# 简单的聊天函数
def chat_with_bot(user_message):
    """简单的聊天函数"""
    responses = {
        "你好": "你好！我是智能客服",
        "再见": "再见，有问题再来！",
        "帮助": "我可以帮你解答问题"
    }
    
    # 返回响应
    if user_message in responses:
        return responses[user_message]
    else:
        return "抱歉，我不太明白"

# 主循环（模拟服务器）
while True:
    user_input = input("\n请输入你的问题（输入exit退出): ")
    if user_input == "exit":
        break
    
    response = chat_with_bot(user_input)
    print(f"🤖 客服: {response}")
    
    # 保存聊天记录
    chat_history.append({
        "user": user_input, 
        "ai": response
    })

print("\n聊天结束，历史记录:")
for chat in chat_history:
    print(f"你: {chat['user']}")
    print(f"🤖: {chat['ai']}")
```

---

## 7. 总结与下一步

### 📝 本节课你学到了什么？
1. 如何安装Python
2. 变量、函数、列表、字典
3. 简单的聊天逻辑
4. 项目的基本结构

### 🎓 下节课你将学到：
- 学习Web框架（FastAPI）
- 理解API概念
- 数据库基础知识

### 📖 学习建议：
1. 多写代码练习
2. 从简单的例子开始
3. 看看项目中的文件，多阅读源码
4. 有问题就问！

---

**恭喜完成第一课！🎉
