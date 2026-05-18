# RAG 智能客服 - Python 入门教程 3：数据库与持久化

## 📚 目录
1. [什么是数据库
2. [SQLite入门（最简单的数据库
3. [项目中的数据库
4. [SQLAlchemy ORM
5. [Redis缓存
6. [向量数据库（ChromaDB
7. [总结与实践

---

## 1. 什么是数据库？

### 💾 为什么需要数据库？

想象一下，如果没有数据库，我们的数据：
- 程序一关闭就丢失了
- 很难查找和筛选
- 多人同时访问会有问题

数据库帮我们安全、高效地存储数据！

### 🗃️ 常见的数据库类型

在我们的项目中使用了这些：
1. **PostgreSQL** - 主数据库（存用户、企业、对话历史
2. **Redis** - 缓存数据库（存临时数据、会话
3. **ChromaDB** - 向量数据库（存文档和语义检索

---

## 2. SQLite入门

我们先从最简单的数据库开始！SQLite是一个文件数据库，不需要安装服务器，非常适合学习。

### 📝 你的第一个SQLite程序

创建 `first_sqlite.py`：

```python
import sqlite3

# 1. 创建/连接到数据库文件
conn = sqlite3.connect('first_database.db')
cursor = conn.cursor()

print("✅ 数据库连接成功！")

# 2. 创建表
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    age INTEGER
)
''')

print("✅ 表创建成功！")

# 3. 插入数据
cursor.execute(
    "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
    ("张三", "zhangsan@example.com", 25)
)
cursor.execute(
    "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
    ("李四", "lisi@example.com", 30)
)

# 记得提交事务！
conn.commit()
print("✅ 数据插入成功！")

# 4. 查询数据
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()

print("\n📋 用户列表:")
for user in users:
    print(f"ID: {user[0]}, 姓名: {user[1]}, 邮箱: {user[2]}, 年龄: {user[3]}")

# 5. 查询特定用户
cursor.execute("SELECT * FROM users WHERE name = ?", ("张三",))
zhangsan = cursor.fetchone()
print(f"\n🔍 查询结果: {zhangsan}")

# 6. 更新数据
cursor.execute(
    "UPDATE users SET age = ? WHERE name = ?",
    (26, "张三")
)
conn.commit()
print("✅ 数据更新成功！")

# 7. 删除数据
# cursor.execute("DELETE FROM users WHERE name = ?", ("李四",))
# conn.commit()
# print("✅ 数据删除成功！")

# 8. 关闭连接
conn.close()
print("\n👋 数据库连接关闭")
```

运行这个程序：
```bash
python first_sqlite.py
```

---

## 3. 项目中的数据库

让我们看一个项目中的简化版本：
`backend/user-service/database.py` (简化版

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 数据库连接配置
DATABASE_URL = "sqlite:///./user_service.db"

# 2. 创建引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 3. 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 基类
Base = declarative_base()

# 5. 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 4. SQLAlchemy ORM（对象关系映射

### 🏗️ 什么是ORM？

ORM可以让我们用Python对象来操作数据库，而不需要写复杂的SQL语句！

看一个完整的例子：
创建 `orm_example.py`：

```python
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 设置
engine = create_engine('sqlite:///example_orm.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

# 2. 定义模型（表）
class FAQ(Base):
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(200), nullable=False)
    answer = Column(String(500), nullable=False)
    category = Column(String(50), default="其他")
    views = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<FAQ(question='{self.question}')>"

# 3. 创建表
Base.metadata.create_all(engine)

# 4. 使用示例
if __name__ == "__main__":
    # 创建会话
    db = Session()
    
    print("📝 添加FAQ...")
    # 添加新FAQ
    faq1 = FAQ(
        question="如何退货？",
        answer="请在订单页面申请退货",
        category="售后"
    )
    faq2 = FAQ(
        question="配送时间？",
        answer="通常24小时内发货",
        category="配送"
    )
    
    db.add(faq1)
    db.add(faq2)
    db.commit()
    
    print("✅ FAQ添加成功！")
    
    # 查询所有FAQ
    print("\n📋 所有FAQ:")
    all_faqs = db.query(FAQ).all()
    for faq in all_faqs:
        print(f"  [{faq.id}] {faq.question} - {faq.answer}")
    
    # 查询特定分类
    print("\n🔍 售后相关FAQ:")
    service_faqs = db.query(FAQ).filter(FAQ.category == "售后").all()
    for faq in service_faqs:
        print(f"  {faq.question}")
    
    # 更新数据
    faq1.views += 1
    db.commit()
    print(f"\n✅ FAQ '{faq1.question}' 查看次数已更新为 {faq1.views}")
    
    # 关闭
    db.close()
    print("\n👋 数据库会话已关闭")
```

---

## 5. Redis缓存

### ⚡ 为什么需要Redis？

Redis是一个**内存数据库**，特别快！用来存：
- 用户会话
- 临时数据
- 限流信息
- 缓存热点数据

### 🚀 简单的Redis示例

创建 `redis_example.py`：

```python
# 先安装 redis 库
# pip install redis

import redis
import json
from datetime import timedelta

# 1. 连接Redis
r = redis.Redis(
    host='localhost', 
    port=6379, 
    db=0, 
    decode_responses=True
)

print("✅ 连接Redis成功！")

# 2. 设置键值对
r.set('name', '张三')
r.set('age', 25)

print(f"📝 名称: {r.get('name')}")
print(f"📝 年龄: {r.get('age')}")

# 3. 设置过期时间
r.setex('temp_code', timedelta(seconds=10), '123456')
print(f"⏱️ 验证码设置（10秒后过期）: {r.get('temp_code')}")

# 4. 使用列表
r.lpush('chat_history', '你好')
r.lpush('chat_history', '请问配送时间')
r.lpush('chat_history', '谢谢')
print(f"\n💬 最近对话: {r.lrange('chat_history', 0, -1)}")

# 5. 使用哈希（Hash
user_data = {
    'id': 'user_001',
    'name': '小明',
    'email': 'xiaoming@example.com'
}
r.hset('user:user_001', mapping=user_data)
print(f"\n👤 用户信息: {r.hgetall('user:user_001')}")

# 6. 计数器
r.set('counter', 0)
r.incr('counter')
r.incr('counter')
r.incr('counter')
print(f"\n🔢 计数器: {r.get('counter')}")

# 7. 完整会话示例
session_id = 'session_123'
session_data = {
    'user_id': 'user_456',
    'state': 'active',
    'last_message': '你好'
}
r.setex(f"session:{session_id}", timedelta(hours=24), json.dumps(session_data))
print(f"\n💾 会话已存储")

# 8. 获取会话
loaded_session = json.loads(r.get(f"session:{session_id}"))
print(f"🔄 会话已加载: {loaded_session}")

print("\n✅ Redis示例完成！")
```

---

## 6. 向量数据库（ChromaDB

### 🧠 什么是向量数据库？

普通数据库存数据和文本，但向量数据库存的是**数值向量**，可以：
- 按语义搜索
- 找到相似的内容
- RAG（检索增强生成）的关键

创建 `chroma_example.py`：

```python
# 安装 chromadb
# pip install chromadb

import chromadb
from chromadb.utils import embedding_functions

print("🎯 向量数据库示例")

# 1. 创建客户端
client = chromadb.Client()

# 2. 创建/获取集合
collection = client.create_collection(name="knowledge_base")

print("✅ 集合创建成功！")

# 3. 添加一些文档到知识库
documents = [
    "这是关于产品退换货政策的说明",
    "产品通常在24小时内发货，快递需要3-5天",
    "客服工作时间是9:00-18:00",
    "我们提供7天无理由退货"
]
ids = ["doc1", "doc2", "doc3", "doc4"]

collection.add(documents=documents, ids=ids)

print(f"✅ 添加了 {len(documents)} 个文档")

# 4. 搜索相似的文档
query = "我想退货"
results = collection.query(query_texts=[query], n_results=2)

print(f"\n🔍 查询: '{query}'")
print("\n📋 找到的最相关文档:")
for i in range(len(results['ids'][0])):
    doc_id = results['ids'][0][i]
    distance = results['distances'][0][i]
    content = results['documents'][0][i]
    print(f"  {i+1}. [{doc_id}] (相似度: {1-distance:.2f})")
    print(f"     {content}")

# 5. 另一个查询
query2 = "什么时候发货？"
results2 = collection.query(query_texts=[query2], n_results=1)

print(f"\n🔍 查询: '{query2}'")
print(f"📋 最相关答案: {results2['documents'][0][0]}")

print("\n✅ 向量数据库示例完成！")
```

---

## 7. 项目中的完整数据存储架构

```
┌───────────────────────────────────────────────────┐
│                  应用层                            │
└────────────────┬──────────────────────────────────┘
                 │
         ┌───────┼───────┐
         │       │       │
         ▼       ▼       ▼
   PostgreSQL    Redis   ChromaDB
    (主数据)    (缓存)   (向量)
   ┌───────┐   ┌───────┐ ┌───────┐
   │用户表  │   │会话   │ │知识库  │
   │企业表  │   │临时数据│ │文档向量│
   │对话历史│   │限流   │ │相似度  │
   └───────┘   └───────┘ └───────┘
```

---

## 8. 总结与实践

### 📝 这节课你学到了什么？
- SQLite数据库的使用
- SQLAlchemy ORM
- Redis缓存
- 向量数据库ChromaDB
- 项目的三层数据存储架构

### 🎯 练习任务：

1. 创建一个简单的FAQ数据库
2. 使用SQLAlchemy ORM
3. 支持添加、查询、删除FAQ
4. 使用Redis缓存热门查询

### 💡 进阶：

看看项目中的文件，试着理解：
- `backend/user-service/models.py`
- `backend/chat-service/database.py`
- `backend/knowledge-service/vector_store.py`

---

**下节课我们学习微服务架构！🎉
