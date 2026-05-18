# 课程练习代码

这是与教程配套的练习代码，你可以直接运行这些文件来练习！

---

## 📋 练习文件列表

### 第1课：Python基础
- `practice_01_hello.py` - 你好世界！
- `practice_02_functions.py` - 函数练习
- `practice_03_lists_dicts.py` - 列表字典
- `practice_04_simple_chat.py` - 简单聊天

### 第2课：Web开发
- `practice_05_first_api.py` - 第一个API
- `practice_06_simple_chat_api.py` - 聊天API

### 第3课：数据库
- `practice_07_sqlite.py` - SQLite数据库
- `practice_08_orm.py` - ORM示例
- `practice_09_redis.py` - Redis缓存
- `practice_10_complete_faq.py` - 完整FAQ系统

---

## 🚀 如何运行练习

1. 确保你有Python 3.10+
2. 安装必要的包
3. 运行对应练习文件

---

## 📝 练习01: 你好世界

文件名：`practice_01_hello.py`

```python
# 练习01: 你好世界
# 运行这个文件：python practice_01_hello.py

print("=" * 40)
print("🎯 练习01: 你好世界")
print("=" * 40)

# 1. 简单打印
print("\n1. 基础打印:")
print("你好，世界！")
print("欢迎学习RAG智能客服项目！")

# 2. 变量
name = "小明"
age = 25
course = "Python入门"
print(f"\n2. 变量:")
print(f"我是{name}，今年{age}岁，正在学习{course}")

# 3. 简单运算
a = 10
b = 20
print(f"\n3. 简单计算:")
print(f"{a} + {b} = {a + b}")
print(f"{a} * {b} = {a * b}")

# 4. 条件语句
print(f"\n4. 条件语句:")
if age >= 18:
    print(f"{name} 是成年人")
else:
    print(f"{name} 还没成年")

# 5. 循环
print(f"\n5. 循环:")
for i in range(5):
    print(f"  第{i}次: 你好！")

print("\n✅ 练习01完成！")
```

---

## 📝 练习02: 函数

文件名：`practice_02_functions.py`

```python
# 练习02: 函数
# 运行: python practice_02_functions.py

print("=" * 40)
print("🎯 练习02: 函数")
print("=" * 40)

# 1. 简单函数
print("\n1. 简单函数:")
def greet(name):
    """问候函数"""
    return f"你好，{name}！"
print(greet("张三"))
print(greet("李四"))

# 2. 带返回值的函数
print("\n2. 带返回值的函数:")
def add(a, b):
    return a + b
result = add(5, 3)
print(f"5 + 3 = {result}")

# 3. 多个参数
print("\n3. 聊天函数:")
def chat_response(message):
    """简单的聊天回复"""
    responses = {
        "你好": "你好！我是智能客服",
        "帮助": "我可以帮你解答问题",
        "再见": "再见，有问题再来！"
    }
    return responses.get(message, "抱歉，我不太明白")

print(f" 问: 你好  -> 答: {chat_response('你好')}")
print(f" 问: 帮助  -> 答: {chat_response('帮助')}")
print(f" 问: 其他  -> 答: {chat_response('其他')}")

print("\n✅ 练习02完成！")
```

---

## 📝 练习03: 列表和字典

文件名：`practice_03_lists_dicts.py`

```python
# 练习03: 列表和字典
# 运行: python practice_03_lists_dicts.py

print("=" * 40)
print("🎯 练习03: 列表和字典")
print("=" * 40)

# 1. 列表示例
print("\n1. 列表:")
faq_list = [
    "如何退货？",
    "配送时间？",
    "客服电话？"
]

print("FAQ列表:")
for i, faq in enumerate(faq_list):
    print(f"  {i+1}. {faq}")

# 添加新FAQ
faq_list.append("新的FAQ问题")
print(f"\n添加后列表长度: {len(faq_list)}")

# 2. 字典示例
print("\n2. 字典:")
faq_answers = {
    "如何退货？": "请在订单页面申请退货",
    "配送时间？": "通常24小时内发货",
    "客服电话？": "客服电话是400-123-4567"
}

# 查询FAQ
question = "如何退货？"
answer = faq_answers.get(question, "抱歉，没有找到答案")
print(f"问: {question}")
print(f"答: {answer}")

# 遍历字典
print("\n所有FAQ:")
for q, a in faq_answers.items():
    print(f" Q: {q}")
    print(f" A: {a}")
    print()

print("✅ 练习03完成！")
```

---

## 📝 练习04: 简单聊天

文件名：`practice_04_simple_chat.py`

```python
# 练习04: 简单聊天程序
# 运行: python practice_04_simple_chat.py

print("=" * 40)
print("🤖 练习04: 简单聊天程序")
print("=" * 40)

# 聊天数据存储
chat_history = []

# 聊天回复函数
def get_response(message):
    """获取机器人回复"""
    responses = {
        "你好": "你好！我是智能客服",
        "你叫什么": "我是智能客服",
        "帮助": "我可以帮你解答问题",
        "再见": "再见，有问题再来！"
    }
    return responses.get(message, "抱歉，我不太明白")

print("\n🤖 你好！我是智能客服，输入 'exit' 退出")
print("-" * 40)

while True:
    # 获取用户输入
    user_input = input("\n你: ").strip()
    
    if user_input.lower() == 'exit':
        print("🤖 再见！")
        break
    
    # 获取回复
    ai_response = get_response(user_input)
    print(f"🤖: {ai_response}")
    
    # 保存历史
    chat_history.append({
        "user": user_input,
        "ai": ai_response
    })

# 显示历史
if chat_history:
    print("\n" + "=" * 40)
    print("📋 聊天历史:")
    for i, chat in enumerate(chat_history):
        print(f"{i+1}. 你: {chat['user']}")
        print(f"   机器人: {chat['ai']}")

print("\n✅ 练习04完成！")
```

---

## 📝 练习05: 第一个API

文件名：`practice_05_first_api.py`

```python
# 练习05: 第一个API
# 运行: python practice_05_first_api.py
# 访问: http://localhost:8080

from fastapi import FastAPI

app = FastAPI(title="练习05 - 第一个API")

# 根路径
@app.get("/")
async def root():
    return {
        "message": "欢迎来到练习05！",
        "course": "Python入门教程"
    }

# 问候API
@app.get("/greet/{name}")
async def greet(name: str):
    return {
        "greeting": f"你好，{name}！",
        "message": "欢迎使用我们的API"
    }

# 简单计算器
@app.get("/calculate/{a}/{b}")
async def calculate(a: int, b: int):
    return {
        "a": a,
        "b": b,
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "除数不能为0"
    }

# 运行服务器
if __name__ == "__main__":
    import uvicorn
    print("=" * 40)
    print("🚀 API服务器启动在 http://localhost:8080")
    print("📚 API文档: http://localhost:8080/docs")
    print("=" * 40)
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## 📝 练习07: SQLite数据库

文件名：`practice_07_sqlite.py`

```python
# 练习07: SQLite数据库
# 运行: python practice_07_sqlite.py

import sqlite3

print("=" * 40)
print("💾 练习07: SQLite数据库")
print("=" * 40)

# 1. 连接数据库
conn = sqlite3.connect('practice_faq.db')
cursor = conn.cursor()
print("\n1. 数据库连接成功！")

# 2. 创建FAQ表
cursor.execute('''
CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT,
    views INTEGER DEFAULT 0
)
''')
print("2. FAQ表创建成功！")

# 3. 插入示例数据
sample_data = [
    ("如何退货？", "请在订单页面申请退货", "售后"),
    ("配送时间？", "通常24小时内发货", "配送"),
    ("客服电话？", "400-123-4567", "客服")
]

for q, a, c in sample_data:
    cursor.execute(
        "INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)",
        (q, a, c)
    )
conn.commit()
print("3. 示例数据插入成功！")

# 4. 查询所有FAQ
print("\n4. 查询所有FAQ:")
cursor.execute("SELECT * FROM faqs")
all_faqs = cursor.fetchall()
for faq in all_faqs:
    print(f"  [{faq[0]}] {faq[1]}")

# 5. 查询特定分类
category = "售后"
print(f"\n5. 查询 '{category}' 相关FAQ:")
cursor.execute("SELECT * FROM faqs WHERE category = ?", (category,))
service_faqs = cursor.fetchall()
for faq in service_faqs:
    print(f"  Q: {faq[1]}")
    print(f"  A: {faq[2]}")

# 6. 更新查看次数
faq_id = 1
cursor.execute("UPDATE faqs SET views = views + 1 WHERE id = ?", (faq_id,))
conn.commit()
print(f"\n6. FAQ ID {faq_id} 查看次数已更新")

# 7. 关闭连接
conn.close()
print("\n✅ 练习07完成！")
```

---

## 🎯 如何使用这些练习？

1. 创建 `PRACTICE/` 文件夹
2. 将每个练习保存为对应文件
3. 按顺序运行和练习
4. 修改代码，观察结果变化

---

**加油！实践是最好的老师！💪✨
