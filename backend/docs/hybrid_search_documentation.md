# 混合检索系统实现文档

## 概述

本系统实现了 FAQ 匹配 + RAG 检索的混合检索流程，并支持引用来源溯源功能。

## 架构设计

### 混合检索流程

```
用户查询
    ↓
意图识别（可选）
    ↓
FAQ 匹配（PostgreSQL）
    ├─ 精确匹配（question 字段模糊查询）
    ├─ 关键词匹配（keywords 字段）
    └─ 余弦相似度匹配（Trigram 索引）
        ↓
命中 → 直接返回 FAQ 答案（零成本，无需 LLM）
        ↓
未命中 → RAG 检索（ChromaDB）
    ├─ 向量检索
    ├─ 重排序
    └─ LLM 生成
        ↓
响应（含引用来源）
```

## 核心组件

### 1. FAQ 数据库模型（faq_models.py）

**表名**：`faq_table`

**字段**：
- `id`: UUID 主键
- `enterprise_id`: 企业 ID（外键）
- `question`: 用户问题
- `answer`: 标准答案
- `keywords`: 关键词列表（逗号分隔）
- `category`: 分类
- `is_active`: 是否启用
- `hit_count`: 命中次数
- `created_at/updated_at`: 时间戳

**索引**：
- Trigram GIN 索引（用于高效模糊匹配）
- Enterprise ID 索引

### 2. 混合检索引擎（rag.py）

**核心方法**：

#### `retrieve()`
主检索方法，执行混合检索流程：
1. 调用 `_faq_match()` 尝试 FAQ 匹配
2. 如果 FAQ 命中，直接返回结果
3. 如果未命中，调用 `_rag_retrieve()` 执行 RAG 检索

#### `_faq_match()`
FAQ 匹配方法：
1. 精确模糊匹配（`question ilike '%query%'`）
2. Trigram 相似度匹配（`similarity(question, query) > 0.6`）
3. 关键词匹配（`keywords ilike '%query%'`）
4. 命中则更新 `hit_count`，返回答案

#### `_rag_retrieve()`
RAG 检索方法：
1. 调用 Knowledge Service 进行向量检索
2. 应用重排序（如果启用）
3. 格式化来源信息

#### `_format_sources()`
来源格式化方法：
```python
[
    {
        "filename": "产品手册.pdf",
        "page": 15,
        "score": 0.95,
        "chunk_number": 0,
        "content": "..."
    }
]
```

#### `generate_prompt()`
带引用要求的 Prompt 生成：
```python
"""你是一个专业的智能客服助手...
重要要求：
1. 所有回答必须基于提供的上下文信息
2. 回答内容必须引用上下文来源，格式为：[来源: 文档名]
   例如：根据文档，我们的营业时间是周一至周五的9:00-18:00 [来源: 产品手册.pdf]
...
"""
```

## API 端点

### 聊天服务（chat-service）

#### `/api/v1/faqs` [POST]
创建 FAQ 条目
```json
{
    "enterprise_id": "uuid",
    "question": "你们的营业时间是什么时候？",
    "answer": "我们的营业时间是周一至周五的9:00-18:00。",
    "keywords": "营业时间,上班时间,开门时间",
    "category": "运营时间"
}
```

#### `/api/v1/faqs` [GET]
列出 FAQ 条目
查询参数：
- `enterprise_id`（必填）
- `category`（可选）
- `skip`, `limit`（分页）

#### `/api/v1/faqs/test` [POST]
测试 FAQ 匹配

#### `/api/v1/chat/sessions/{session_id}/messages` [POST]
发送消息（核心聊天接口）

**请求**：
```json
{
    "content": "你们的营业时间是什么时候？",
    "user_id": "uuid",
    "enterprise_id": "uuid"
}
```

**响应**（FAQ 命中）：
```json
{
    "message_id": "uuid",
    "role": "assistant",
    "answer": "我们的营业时间是周一至周五的9:00-18:00。",
    "content": "我们的营业时间是周一至周五的9:00-18:00。",
    "sources": [
        {
            "filename": "FAQ Database",
            "page": null,
            "score": 1.0,
            "chunk_number": null
        }
    ],
    "source_type": "faq",
    "llm_called": false,
    "tokens_used": 0
}
```

**响应**（RAG 检索）：
```json
{
    "answer": "根据产品手册，我们的产品型号包括 A1、B2、C3。[来源: 产品手册.pdf]",
    "sources": [
        {
            "filename": "产品手册.pdf",
            "page": 3,
            "score": 0.95,
            "chunk_number": 0,
            "content": "产品型号包括 A1、B2、C3..."
        }
    ],
    "source_type": "rag",
    "llm_called": true,
    "tokens_used": 500
}
```

## 引用来源功能

### 引用格式

LLM 生成回答时，会在引用的内容末尾标记来源：
```
根据产品手册，我们的营业时间是周一至周五的9:00-18:00 [来源: 产品手册.pdf]
```

### 来源数据结构

```python
{
    "filename": "产品手册.pdf",
    "page": 3,
    "score": 0.95,
    "chunk_number": 0,
    "content": "产品手册的一段内容..."
}
```

## 测试方法

### 1. 创建测试 FAQ

```bash
curl -X POST http://localhost:8080/api/v1/faqs \
  -H "Content-Type: application/json" \
  -d '{
    "enterprise_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "你们的营业时间是什么时候？",
    "answer": "我们的营业时间是周一至周五的9:00-18:00。",
    "keywords": "营业时间,上班时间,开门时间",
    "category": "运营时间"
  }'
```

### 2. 测试 FAQ 匹配

```bash
curl -X POST http://localhost:8080/api/v1/faqs/test \
  -d "enterprise_id=550e8400-e29b-41d4-a716-446655440000" \
  -d "query=你们的营业时间是什么时候"
```

### 3. 完整聊天测试

```bash
curl -X POST http://localhost:8080/api/v1/chat/sessions/550e8400-e29b-41d4-a716-446655440000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你们的营业时间是什么时候？",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "enterprise_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

## 成本优化效果

### 场景预估

| 场景 | 原方案 Token 消耗 | 新方案 Token 消耗 | 节省 |
|------|-------------------|-------------------|------|
| 闲聊（你好） | 200 | 0 | 100% |
| FAQ（营业时间） | 500 | 0 | 100% |
| 简单 RAG 查询 | 800 | 800 | 0% |
| 复杂 RAG 查询 | 1500 | 1500 | 0% |

### 实际预估

假设 1000 次/天查询：
- 30% 闲聊/感谢
- 20% FAQ 查询
- 50% RAG 查询

**原方案成本**：(1000 × 平均 800 Token) × 0.002元/Token = 1600元/天

**新方案成本**：(500 × 800 Token) × 0.002元/Token = 800元/天

**每日节省**：800元（50%成本）
**年度节省**：292,000元

## 数据库优化建议

1. **Trigram 扩展**：确保 PostgreSQL 启用 pg_trgm 扩展
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

2. **索引创建**：
```sql
CREATE INDEX idx_faq_question_gin 
ON faq_table USING GIN (question gin_trgm_ops);
```

## 下一步工作

1. 多模态支持（图片、表格 OCR）
2. FAQ 批量导入/导出
3. FAQ 自动学习（从负面反馈中学习）
4. FAQ 问答验证（人工审核）
5. 更多渠道适配（微信、钉钉等）
