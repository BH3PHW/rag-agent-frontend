# 意图识别与路由系统实现文档

## 概述

意图识别与路由系统旨在**拦截闲聊和简单指令，避免每次都调用昂贵的 Qwen 大模型**，从而显著降低 API 调用成本。

**预期成本优化效果：** 节省 30%-50% 的 Token 成本

---

## 架构设计

```
用户消息
    ↓
意图识别层（规则正则 + 轻量级分类）
    ↓
┌─────────────────────────────────────┐
│           意图分类                   │
├─────────────────────────────────────┤
│ GREETING (寒暄) → 直接回复，不调用LLM │
│ THANKS (感谢)   → 直接回复，不调用LLM │
│ FAREWELL (告别) → 直接回复，不调用LLM │
│ ORDER_QUERY     → 业务接口，不调用LLM │
│ HUMAN (转人工)  → 标记告警，不调用LLM │
│ RAG (复杂咨询)  → 完整RAG + LLM调用   │
└─────────────────────────────────────┘
    ↓
响应返回 + 成本统计记录
```

---

## 核心组件

### 1. IntentRouter 类

**文件位置：** [intent_router.py](file:///workspace/backend-rag-customer-service/chat-service/intent_router.py)

#### 主要功能

| 方法 | 说明 |
|------|------|
| `classify(query)` | 意图分类主方法 |
| `_make_decision()` | 生成路由决策 |
| `calculate_cost_saved()` | 计算成本节省 |
| `log_route()` | 记录路由日志 |
| `get_cost_stats()` | 获取成本统计 |

#### 意图类型

```python
class IntentType(Enum):
    GREETING = "greeting"           # 寒暄
    THANKS = "thanks"              # 感谢
    FAREWELL = "farewell"          # 告别
    ORDER_QUERY = "order_query"     # 订单查询
    PRODUCT_QUERY = "product_query" # 产品查询
    COMPLAINT = "complaint"        # 投诉
    FAQ = "faq"                    # FAQ匹配
    RAG = "rag"                    # RAG检索（复杂咨询）
    HUMAN = "human"                # 转人工
    UNKNOWN = "unknown"            # 未知
```

#### 成本等级

```python
class CostTier(Enum):
    FREE = 0        # 免费（规则响应）
    LOW = 1         # 低成本（简单处理）
    MEDIUM = 2      # 中等成本（部分LLM调用）
    HIGH = 3        # 高成本（完整RAG+LLM）
```

#### 路由决策数据结构

```python
@dataclass
class IntentDecision:
    intent: IntentType           # 意图类型
    cost_tier: CostTier         # 成本等级
    should_use_llm: bool        # 是否调用 LLM
    should_use_rag: bool        # 是否调用 RAG
    should_escalate: bool       # 是否转人工
    confidence: float           # 置信度
    response: Optional[str]      # 预设回复（可直接回复时）
    extracted_entities: Dict     # 提取的实体
    reasoning: str              # 决策原因
```

---

## FastAPI 集成

### 方式一：依赖注入

**文件位置：** [intent_integration.py](file:///workspace/backend-rag-customer-service/chat-service/intent_integration.py)

```python
from fastapi import Depends

async def intent_route_dependency(
    query: str
) -> IntentDecision:
    """FastAPI 依赖注入：意图路由"""
    router = get_intent_router()
    decision = router.classify(query)
    return decision

@app.post("/chat")
async def chat(
    query: str,
    decision: IntentDecision = Depends(intent_route_dependency)
):
    if decision.response:
        return {"response": decision.response}

    # 调用 LLM/RAG
    return {"type": "need_llm", "intent": decision.intent}
```

### 方式二：直接集成（当前实现）

在 `send_message` 接口中直接调用：

```python
@app.post("/api/v1/chat/sessions/{session_id}/messages")
async def send_message(session_id, content, ...):
    # 意图路由层
    intent_router = get_intent_router()
    intent_decision = intent_router.classify(content)

    # 直接回复（闲聊、寒暄等）
    if intent_decision.response:
        return {
            "content": intent_decision.response,
            "llm_called": False
        }

    # 继续 RAG + LLM 流程
    ...
```

---

## API 接口

### 1. 路由成本统计

**接口：** `GET /api/v1/routing/stats`

**响应示例：**
```json
{
    "total_requests": 1000,
    "total_tokens_saved": 350000,
    "total_cost_saved": 1.6,
    "llm_call_rate": 35.5,
    "intent_distribution": {
        "greeting": 150,
        "thanks": 80,
        "farewell": 60,
        "order_query": 120,
        "rag": 355,
        "human": 35,
        "complaint": 200
    }
}
```

### 2. 意图路由测试

**接口：** `POST /api/v1/routing/test`

**请求参数：**
```json
{
    "query": "你好"
}
```

**响应示例：**
```json
{
    "intent": "greeting",
    "cost_tier": "FREE",
    "should_use_llm": false,
    "should_use_rag": false,
    "should_escalate": false,
    "confidence": 0.95,
    "response": "您好！我是智能客服，很高兴为您服务。请问有什么可以帮您？",
    "extracted_entities": {},
    "reasoning": "闲聊寒暄，使用预设回复"
}
```

---

## 规则匹配示例

### 寒暄/闲聊

| 输入 | 响应 | 成本 |
|------|------|------|
| 你好 | 预设回复 | 免费 |
| 您好！ | 预设回复 | 免费 |
| 在吗？ | 预设回复 | 免费 |

### 感谢/告别

| 输入 | 响应 | 成本 |
|------|------|------|
| 谢谢 | 预设回复 | 免费 |
| 感谢 | 预设回复 | 免费 |
| 再见 | 预设回复 | 免费 |
| 拜拜 | 预设回复 | 免费 |

### 业务查询

| 输入 | 响应 | 成本 |
|------|------|------|
| 查订单 | 提取订单号，调用业务接口 | 低 |
| 我的订单 | 提取手机号，调用业务接口 | 低 |
| 什么时候发货 | 调用物流接口 | 低 |

### 转人工

| 输入 | 响应 | 成本 |
|------|------|------|
| 转人工 | 标记告警，转接人工 | 低 |
| 我要投诉 | 标记告警，转接人工 | 低 |
| 真人服务 | 标记告警，转接人工 | 低 |

### 复杂咨询（调用LLM）

| 输入 | 响应 | 成本 |
|------|------|------|
| 你们的退款政策是什么？ | RAG + LLM | 高 |
| 产品A和B有什么区别？ | RAG + LLM | 高 |
| 如何使用XX功能？ | RAG + LLM | 高 |

---

## 成本计算

### Token 成本估算

```python
COST_PER_TOKEN = 0.002  # 每 Token 成本（元）
AVG_QUERY_TOKENS = 500   # 平均查询 Token 数
AVG_RESPONSE_TOKENS = 300  # 平均响应 Token 数

# 不经路由直接调用 LLM 的成本
full_llm_cost = (500 + 300) * 0.002 = 1.6 元/请求
```

### 成本节省示例

| 意图类型 | 成本等级 | 节省比例 | 节省金额/请求 |
|---------|---------|---------|--------------|
| 寒暄/感谢/告别 | 免费 | 100% | 1.6 元 |
| 订单查询 | 低成本 | 70% | 1.12 元 |
| 投诉 | 中等 | 50% | 0.8 元 |
| 复杂咨询 | 高成本 | 0% | 0 元 |

### 成本优化效果

假设 1000 次请求分布：
- 寒暄 30% → 300 次 × 1.6 = 480 元
- 感谢 15% → 150 次 × 1.6 = 240 元
- 告别 10% → 100 次 × 1.6 = 160 元
- 订单查询 10% → 100 次 × 1.12 = 112 元
- 复杂咨询 35% → 350 次 × 0 = 0 元

**总节省：992 元 / 1000 次请求**

---

## 日志记录

### 路由日志结构

```python
@dataclass
class RouteLog:
    request_id: str        # 请求ID
    timestamp: datetime     # 时间戳
    query: str             # 用户查询
    intent: IntentType     # 意图类型
    cost_tier: CostTier    # 成本等级
    llm_called: bool     # 是否调用了 LLM
    tokens_used: int       # 使用的 Token 数
    estimated_cost_saved: float  # 预估节省成本
    response_time_ms: int  # 响应时间
```

### 日志用途

1. **成本分析**：统计各意图类型的分布和节省
2. **性能监控**：监控响应时间和 LLM 调用率
3. **问题排查**：追踪特定请求的处理路径
4. **规则优化**：基于日志调整规则匹配

---

## 扩展计划

### 短期扩展

1. **实体识别增强**
   - 集成 NER 模型提取更丰富的实体
   - 支持自定义实体类型

2. **规则可配置化**
   - 将规则配置移至数据库
   - 支持运行时修改规则

### 长期扩展

1. **小模型分类**
   - 使用 BGE-M3 或 Text2Vec 进行语义分类
   - 替代部分正则规则

2. **学习优化**
   - 基于反馈数据自动优化规则
   - A/B 测试不同路由策略

3. **多语言支持**
   - 扩展支持英文、日文等语言
   - 跨语言意图识别

---

## 文件清单

| 文件 | 说明 |
|------|------|
| chat-service/intent_router.py | 意图路由核心类 |
| chat-service/intent_integration.py | FastAPI 集成示例 |
| chat-service/main.py | 完整集成实现 |

---

## 使用指南

### 启动服务

```bash
cd /workspace/backend-rag-customer-service
docker-compose up -d
```

### 测试意图路由

```bash
# 测试寒暄
curl -X POST http://localhost:8003/api/v1/routing/test \
  -d "query=你好"

# 测试订单查询
curl -X POST http://localhost:8003/api/v1/routing/test \
  -d "query=查一下我的订单"

# 测试复杂咨询
curl -X POST http://localhost:8003/api/v1/routing/test \
  -d "query=你们公司的退款政策是什么"
```

### 查看成本统计

```bash
curl http://localhost:8003/api/v1/routing/stats
```

### 查看 API 文档

访问：http://localhost:8003/docs

---

## 注意事项

1. **规则优先级**：规则按定义顺序匹配，确保优先级高的规则在前
2. **响应多样性**：预设回复使用随机选择，增加用户体验
3. **日志保留**：日志最多保留 10000 条，自动清理旧日志
4. **成本估算**：成本节省为估算值，实际节省取决于具体实现

---

## 技术栈

- Python 3.11
- FastAPI 0.109.0
- SQLAlchemy 2.0.25
- 正则表达式（规则匹配）
- 阿里云百炼 Qwen API（LLM 调用）

---

*文档版本：1.0*
*最后更新：2024-01-15*
