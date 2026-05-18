# 问答质量评估功能实现文档

## 功能概述
本功能实现了用户反馈收集和低质量回答检测，帮助企业持续优化客服系统。

---

## 实现内容

### 1. 数据库设计

#### feedback 表
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | NOT NULL |
| message_id | UUID | 关联对话消息 | NOT NULL |
| user_id | UUID | 用户ID | NOT NULL |
| rating | String(20) | 评分 ("thumbs_up" | "thumbs_down") | NOT NULL |
| reason | Text | 点踩原因（可选） | NULLABLE |
| created_at | DateTime | 创建时间 | NOT NULL |

#### unmatched_questions 表
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | NOT NULL |
| session_id | UUID | 会话ID | NOT NULL |
| user_id | UUID | 用户ID | NOT NULL |
| question | Text | 用户提问 | NOT NULL |
| retrieval_score | Float | 检索相似度分数 | NOT NULL |
| created_at | DateTime | 创建时间 | NOT NULL |

**文件位置：**
[quality_models.py](file:///workspace/backend-rag-customer-service/chat-service/quality_models.py)

---

### 2. API 接口开发

#### POST /api/v1/feedback
接收前端传来的评分和原因，存入数据库。

**请求参数：**
- `message_id` (UUID, required): 消息ID
- `user_id` (UUID, required): 用户ID  
- `rating` (String, required): "thumbs_up" | "thumbs_down"
- `reason` (String, optional): 点踩原因

**示例请求：**
```bash
curl -X POST http://localhost:8080/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "rating": "thumbs_down",
    "reason": "回答不准确，信息过时"
  }'
```

**示例响应：**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "rating": "thumbs_down",
  "reason": "回答不准确，信息过时",
  "created_at": "2024-01-15T12:00:00Z"
}
```

**文件位置：**
[chat-service/main.py](file:///workspace/backend-rag-customer-service/chat-service/main.py)

---

#### GET /api/v1/analytics/low-quality
查询点踩率最高的 Top 10 问题，供管理员后台调用。

**示例响应：**
```json
[
  {
    "question": "你们公司的退款政策是什么？",
    "thumbs_down_count": 8,
    "total_count": 12,
    "thumbs_down_rate": 0.6667
  },
  {
    "question": "产品什么时候会更新？",
    "thumbs_down_count": 5,
    "total_count": 10,
    "thumbs_down_rate": 0.5
  }
]
```

**文件位置：**
[chat-service/main.py](file:///workspace/backend-rag-customer-service/chat-service/main.py)

---

### 3. RAG 检索逻辑集成

**功能说明：**
当 ChromaDB 返回的最高检索相似度分数低于 0.7 时，异步将该用户提问写入 `unmatched_questions` 表。

**实现位置：**
[chat-service/main.py](file:///workspace/backend-rag-customer-service/chat-service/main.py)

**核心代码片段：**
```python
# 计算最高检索相似度分数
max_score = 0
if chunks:
    max_score = max(1 - chunk.get("distance", 0) for chunk in chunks)

# 如果最高相似度低于 0.7，则异步记录该问题
if max_score < 0.7:
    background_tasks.add_task(
        log_unmatched_question,
        session_id,
        user_id,
        content,
        max_score
    )
```

---

## 使用指南

### 启动服务
```bash
cd /workspace/backend-rag-customer-service
docker-compose up -d
```

### 验证功能
1. **提交反馈：**
   ```bash
   curl -X POST http://localhost:8080/api/v1/feedback \
     -H "Content-Type: application/json" \
     -d '{
       "message_id": "your-message-id",
       "user_id": "your-user-id",
       "rating": "thumbs_down",
       "reason": "测试原因"
     }'
   ```

2. **查看低质量问题：**
   ```bash
   curl http://localhost:8080/api/v1/analytics/low-quality
   ```

3. **触发未命中检测：**
   输入一个没有相关知识的问题，如 "不存在的产品型号"，系统会自动记录到 `unmatched_questions` 表。

---

## 文件变更记录

| 文件 | 操作 | 说明 |
|------|------|------|
| chat-service/quality_models.py | 新增 | 新增两个表的模型定义 |
| chat-service/main.py | 修改 | 新增 API 接口，集成 RAG 逻辑 |
| chat-service/__init__.py | 新增 | 确保模型被正确导入 |

---

## 注意事项
- 所有表会在服务启动时自动创建
- 低质量问题记录是异步的，不会影响用户体验
- 评分必须是 "thumbs_up" 或 "thumbs_down"，点踩必须填写原因
