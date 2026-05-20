# 第3章：RAG检索与重排序优化

> 🎯 **学习目标**：深入理解RAG引擎的混合检索流程，掌握重排序机制的原理与实现
> 💡 **学习重点**：FAQ匹配与向量检索的结合策略、交叉编码器的应用、引用来源标注

---

## 3.1 RAG引擎工作原理

### 3.1.1 混合检索的设计思路

```
┌─────────────────────────────────────────────────────────────────────┐
│                    为什么需要混合检索？                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  问题：单一检索方式的局限性                                          │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │                                                          │      │
│  │  场景1：简单FAQ问题                                      │      │
│  │  用户问："你们几点下班？"                                │      │
│  │  ├───────────────────────────────────────────────────┤      │
│  │  │ 用向量检索：                                         │      │
│  │  │ 1. 向量化问题 → 计算开销                            │      │
│  │  │ 2. 向量数据库搜索 → IO开销                          │      │
│  │  │ 3. 调用LLM生成答案 → 昂贵                           │      │
│  │  │                                                          │      │
│  │  │ 用FAQ匹配：                                           │      │
│  │  │ 1. 数据库关键词搜索 → 快速                            │      │
│  │  │ 2. 直接返回预设答案 → 零成本                          │      │
│  │  │                                                          │      │
│  │  │ ✅ 结论：简单问题用FAQ更高效                          │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  场景2：复杂问题                                                    │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │                                                          │      │
│  │  用户问："第三季度的退换货政策与第二季度相比有什么变化？"  │      │
│  │  ├───────────────────────────────────────────────────┤      │
│  │  │ FAQ：可能没有这个特定问题的预设答案                  │      │
│  │  │ 向量检索：可以从多个文档片段中找到相关信息             │      │
│  │  │                                                          │      │
│  │  │ ✅ 结论：复杂问题用RAG更准确                          │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  最佳方案：混合检索策略                                            │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │                                                          │      │
│  │  1. 先用FAQ快速匹配                                      │      │
│  │  2. 匹配度足够高 → 直接返回FAQ答案                        │      │
│  │  3. 匹配度不够 → 进入RAG流程                              │      │
│  │                                                          │      │
│  │  ✅ 兼顾效率与准确性                                      │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.1.2 混合检索完整流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    混合检索完整流程                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                      用户问题                                        │
│                         │                                           │
│                         ▼                                           │
│          ┌──────────────────────────────────┐                     │
│          │   步骤1：FAQ匹配（PostgreSQL）    │                     │
│          │   - 关键词模糊匹配               │                     │
│          │   - 语义相似度计算               │                     │
│          └──────────────┬───────────────────┘                     │
│                         │                                           │
│                         ▼                                           │
│              匹配度 ≥ 阈值(0.85)？                                 │
│              ┌───────┬───────┐                                    │
│              │   是  │   否  │                                    │
│              └───┬───┴───┬───┘                                    │
│                  │       │                                        │
│   ┌──────────────┘       └─────────────────┐                     │
│   │                                         │                     │
│   ▼                                         ▼                     │
│  ┌─────────────────┐        ┌───────────────────────────┐         │
│  │  返回FAQ答案    │        │  步骤2：向量检索(ChromaDB)  │         │
│  │  来源标注: FAQ  │        │  - 问题向量化              │         │
│  └─────────────────┘        │  - Top-K相似片段          │         │
│                              └───────────────┬───────────┘         │
│                                              │                     │
│                                              ▼                     │
│                              ┌───────────────────────────┐         │
│                              │  步骤3：重排序(Rerank)     │         │
│                              │  - 交叉编码器精排         │         │
│                              │  - 综合评分计算           │         │
│                              └───────────────┬───────────┘         │
│                                              │                     │
│                                              ▼                     │
│                              ┌───────────────────────────┐         │
│                              │  步骤4：引用来源标注       │         │
│                              │  - 文档名                 │         │
│                              │  - 页码                   │         │
│                              │  - 评分                   │         │
│                              └───────────────┬───────────┘         │
│                                              │                     │
│                                              ▼                     │
│                              ┌───────────────────────────┐         │
│                              │  步骤5：构造提示词         │         │
│                              │  - 引用格式: [来源:xxx]   │         │
│                              └───────────────┬───────────┘         │
│                                              │                     │
│                                              ▼                     │
│                              ┌───────────────────────────┐         │
│                              │  步骤6：LLM生成答案        │         │
│                              └───────────────────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3.2 核心代码实现详解

### 3.2.1 RAGEngine 类结构

**文件位置**：`backend/chat-service/rag.py`

```python
class RAGEngine:
    """RAG engine with Hybrid Search and Citation support"""
    
    def __init__(self):
        self.knowledge_service_url = settings.KNOWLEDGE_SERVICE_URL
        self.faq_threshold = 0.85  # FAQ匹配阈值
        self.rag_threshold = 0.7   # RAG片段阈值
```

**工程化思维**：
- **配置外置**：阈值通过 settings 管理，便于调优
- **微服务架构**：通过 API 调用 knowledge-service，职责分离
- **单例模式**：通过 get_rag_engine() 获取单例，避免重复初始化

### 3.2.2 FAQ匹配实现

```python
async def _faq_match(
    self,
    enterprise_id: str,
    query: str
) -> Optional[Dict[str, Any]]:
    """
    Step 1: FAQ Matching via Knowledge Service API.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.knowledge_service_url}/api/v1/faqs/match",
                params={
                    "enterprise_id": enterprise_id,
                    "query": query
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("matched"):
                    faq = data.get("faq")
                    return {
                        "source_type": "faq",
                        "answer": faq.get("answer"),
                        "sources": [{
                            "filename": "FAQ Database",
                            "page": None,
                            "score": 1.0,
                            "chunk_number": None
                        }],
                        "is_faq": True,
                        "faq_id": faq.get("id"),
                        "chunks": []
                    }
        
        return None
    except Exception as e:
        print(f"FAQ matching via API error: {e}")
        return None
```

**最佳实践**：
1. **超时控制**：设置 30 秒超时，避免阻塞
2. **异常处理**：捕获所有异常，保证服务不崩溃
3. **降级策略**：FAQ 匹配失败时，自动降级到 RAG 检索

### 3.2.3 RAG检索实现

```python
async def _rag_retrieve(
    self,
    enterprise_id: str,
    query: str,
    knowledge_base_ids: Optional[List[str]] = None,
    top_k: int = None,
    enable_rerank: bool = True,
    use_cross_encoder: bool = True
) -> Dict[str, Any]:
    """
    Step 2: RAG Retrieval from knowledge service.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.knowledge_service_url}/api/v1/retrieve",
                params={
                    "enterprise_id": enterprise_id,
                    "query": query,
                    "top_k": top_k or settings.TOP_K,
                    "enable_rerank": enable_rerank,
                    "use_cross_encoder": use_cross_encoder
                },
                json={"knowledge_base_ids": knowledge_base_ids} if knowledge_base_ids else None
            )
            response.raise_for_status()
            data = response.json()
            chunks = data.get("chunks", [])
            
            # 格式化来源信息
            sources = self._format_sources(chunks)
            
            return {
                "source_type": "rag",
                "answer": None,
                "sources": sources,
                "chunks": chunks,
                "is_faq": False
            }
    except Exception as e:
        print(f"Failed to retrieve from knowledge service: {e}")
        return {
            "source_type": "rag",
            "answer": None,
            "sources": [],
            "chunks": [],
            "is_faq": False
        }
```

**关键设计点**：
- **参数可配置**：top_k、enable_rerank、use_cross_encoder 都可配置
- **多知识库支持**：可指定 knowledge_base_ids，实现租户隔离
- **优雅降级**：检索失败时返回空结果，不影响主流程

### 3.2.4 引用来源格式化

```python
def _format_sources(self, chunks: List[Dict]) -> List[Dict[str, Any]]:
    """
    Format chunks into structured sources list.
    
    Output format:
    [
        {
            "filename": "product_manual.pdf",
            "page": 15,
            "score": 0.95,
            "chunk_number": 0,
            "content": "..."
        }
    ]
    """
    sources = []
    for i, chunk in enumerate(chunks):
        metadata = chunk.get("metadata", {})
        filename = metadata.get("filename", "Unknown")
        page = metadata.get("page")
        distance = chunk.get("distance", 0)
        score = 1 - distance  # distance 转 score
        
        sources.append({
            "filename": filename,
            "page": page,
            "score": round(score, 3),
            "chunk_number": i,
            "content": chunk.get("content", "")[:100] + "..."
        })
    
    return sources
```

**产品化思维**：
- **距离转评分**：distance 是 [0,1]，score = 1 - distance 更直观
- **内容截断**：只显示前 100 字符，避免响应过大
- **丰富元数据**：包含文件名、页码、评分，便于用户溯源

---

## 3.3 重排序(Rerank)机制详解

### 3.3.1 为什么需要重排序？

```
┌─────────────────────────────────────────────────────────────────────┐
│                    向量检索的局限性                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  问题：向量相似度 ≠ 语义相关性                                      │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │                                                          │      │
│  │  用户问题："如何申请退款？"                              │      │
│  │                                                          │      │
│  │  向量检索结果（按相似度排序）：                           │      │
│  │  1. "退款流程：点击订单详情..."  相似度 0.92  ✅ 相关     │      │
│  │  2. "退货政策：收到商品7天内..."  相似度 0.88  ✅ 相关     │      │
│  │  3. "换货说明：尺码不合适..."      相似度 0.85  ❌ 不相关   │      │
│  │  4. "发票开具：订单完成后..."      相似度 0.82  ❌ 不相关   │      │
│  │  5. "物流查询：输入运单号..."      相似度 0.80  ❌ 不相关   │      │
│  │                                                          │      │
│  │  问题：第3-5个结果虽然向量相似，但语义不相关              │      │
│  │                                                          │      │
│  │  解决方案：重排序！                                       │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3.2 交叉编码器 vs 双重编码器

```
┌─────────────────────────────────────────────────────────────────────┐
│              双重编码器 vs 交叉编码器                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  双重编码器（Bi-Encoder）：                                         │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │                                                          │      │
│  │  查询    →  [Embedding模型]  →  向量Q                    │      │
│  │  文档1   →  [Embedding模型]  →  向量D1                   │      │
│  │  文档2   →  [Embedding模型]  →  向量D2                   │      │
│  │  ...                                                     │      │
│  │                                                          │      │
│  │  相似度 = cos(Q, D1), cos(Q, D2), ...                   │      │
│  │                                                          │      │
│  │  ✅ 优点：文档向量可预计算，检索速度快                    │      │
│  │  ❌ 缺点：相似度计算不够精确                              │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  交叉编码器（Cross-Encoder）：                                      │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │                                                          │      │
│  │  [查询 + 文档1]  →  [Cross-Encoder]  →  分数S1          │      │
│  │  [查询 + 文档2]  →  [Cross-Encoder]  →  分数S2          │      │
│  │  ...                                                     │      │
│  │                                                          │      │
│  │  ✅ 优点：同时考虑查询和文档，评分更精确                  │      │
│  │  ❌ 缺点：需要实时计算，速度较慢                          │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
│  最佳实践：两阶段检索                                              │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │                                                          │      │
│  │  阶段1：双重编码器粗排 → 快速召回 Top-50                │      │
│  │  阶段2：交叉编码器精排 → 精确排序 Top-5                 │      │
│  │                                                          │      │
│  │  ✅ 兼顾速度与精度                                      │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3.3 重排序代码实现

**文件位置**：`backend/knowledge-service/rerank.py`

```python
class Reranker:
    """Rerank retrieved chunks using cross-encoder model"""

    def __init__(
        self,
        model_name: str = "shibing624/text2vec-base-chinese",
        use_pretrained: bool = True
    ):
        self.model_name = model_name
        self.use_pretrained = use_pretrained
        self._model = None

    @property
    def model(self):
        """Lazy load cross-encoder model"""
        if self._model is None:
            try:
                self._model = CrossEncoder(
                    self.model_name,
                    max_length=512
                )
            except Exception as e:
                print(f"Warning: Failed to load cross-encoder model: {e}")
                self._model = None
        return self._model
```

**工程化亮点**：
- **懒加载**：模型只在第一次使用时加载，节省内存
- **降级策略**：模型加载失败时，`_model` 为 None，后续使用 SimpleReranker 降级

```python
def rerank(
    self,
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 5,
    batch_size: int = 32
) -> List[Dict[str, Any]]:
    """
    Rerank chunks using cross-encoder model.
    """
    if not chunks or not self.model:
        return chunks[:top_k]

    try:
        chunk_texts = [chunk.get("content", "") for chunk in chunks]
        query_chunk_pairs = [[query, text] for text in chunk_texts]

        scores = self.model.predict(
            query_chunk_pairs,
            batch_size=batch_size,
            show_progress_bar=False
        )

        if isinstance(scores, np.ndarray):
            scores = scores.tolist()

        for i, chunk in enumerate(chunks):
            chunk["rerank_score"] = float(scores[i])
            chunk["original_score"] = chunk.get("distance", 0.0)
            chunk["combined_score"] = (
                0.4 * (1 - chunk.get("distance", 0)) +
                0.6 * float(scores[i])
            )

        reranked = sorted(
            chunks,
            key=lambda x: x.get("combined_score", 0),
            reverse=True
        )

        for i, chunk in enumerate(reranked):
            chunk["rerank_rank"] = i + 1

        return reranked[:top_k]

    except Exception as e:
        print(f"Reranking failed: {e}, returning original order")
        return chunks[:top_k]
```

**关键设计**：
1. **综合评分**：combined_score = 0.4 * 向量分数 + 0.6 * 重排序分数
2. **权重可调**：可以根据实际效果调整权重比例
3. **排序信息**：保留 rerank_rank，便于调试和评估

### 3.3.4 简单重排序器（降级方案）

```python
class SimpleReranker:
    """Simple rule-based reranker (fallback when cross-encoder unavailable)"""

    def __init__(self):
        self.exact_match_weight = 2.0
        self.keyword_weights = {
            "how": 1.5,
            "what": 1.5,
            "why": 1.5,
            "多少": 1.3,
            "怎么": 1.3,
            "什么": 1.3,
        }

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Simple rule-based reranking.
        """
        if not chunks:
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())

        for chunk in chunks:
            content_lower = chunk.get("content", "").lower()

            exact_matches = sum(
                1 for word in query_words
                if word in content_lower
            )

            keyword_bonus = 0.0
            for keyword, weight in self.keyword_weights.items():
                if keyword in query_lower and keyword in content_lower:
                    keyword_bonus += weight

            base_score = 1 - chunk.get("distance", 0)

            rerank_score = (
                base_score +
                (exact_matches * self.exact_match_weight) +
                keyword_bonus
            )

            chunk["rerank_score"] = rerank_score
            chunk["combined_score"] = rerank_score

        reranked = sorted(
            chunks,
            key=lambda x: x.get("combined_score", 0),
            reverse=True
        )

        for i, chunk in enumerate(reranked):
            chunk["rerank_rank"] = i + 1

        return reranked[:top_k]
```

**产品化思维**：
- **降级方案**：即使没有深度学习模型，也能通过规则提供基本的重排序
- **关键词权重**：针对疑问词给予更高权重，符合问答场景
- **精确匹配加分**：完全匹配的关键词给予更高权重

---

## 3.4 引用来源标注与提示词构造

### 3.4.1 上下文格式化

```python
def format_context(self, chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks into context with citations"""
    if not chunks:
        return ""
    
    context = "相关上下文：\n\n"
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("filename", "Unknown")
        
        context += f"[来源{i}] 文档：{source}\n"
        
        if chunk.get("metadata", {}).get("page"):
            context += f"页码：{chunk['metadata']['page']}\n"
        
        if "rerank_rank" in chunk:
            context += f"重排序：第{chunk['rerank_rank']}名\n"
            if "combined_score" in chunk:
                context += f"综合评分：{chunk['combined_score']:.3f}\n"
        
        context += f"内容：{chunk['content']}\n\n"
    
    return context
```

### 3.4.2 提示词生成

```python
def generate_prompt(
    self,
    query: str,
    context: str,
    history: List[Dict[str, str]] = None
) -> str:
    """
    Generate prompt with citation requirements.
    
    System Prompt requires LLM to cite sources in answers.
    """
    prompt = f"""你是一个专业的智能客服助手。请根据提供的上下文信息来回答用户的问题。

重要要求：
1. 所有回答必须基于提供的上下文信息，不能编造信息
2. 回答内容必须引用上下文来源，格式为：[来源: 文档名]
   例如：根据文档，我们的营业时间是周一至周五的9:00-18:00 [来源: 产品手册.pdf]
3. 如果上下文信息不足，请诚实告知用户无法回答该问题
4. 回答要简洁明了，避免冗长

{context}

用户问题：{query}

"""
    
    if history:
        prompt += "对话历史：\n"
        for msg in history[-5:]:
            role = "用户" if msg["role"] == "user" else "助手"
            prompt += f"{role}：{msg['content']}\n"
        prompt += "\n"
    
    prompt += "请给出回答（必须标注引用来源）："
    
    return prompt
```

**产品化亮点**：
1. **强制引用**：在提示词中明确要求 LLM 标注来源
2. **示例引导**：提供具体的引用格式示例
3. **防幻觉**：明确禁止编造信息
4. **历史截断**：只保留最近 5 轮对话，避免上下文过长

---

## 3.5 最佳实践总结

### 3.5.1 检索优化

| 优化项 | 说明 | 推荐值 |
|--------|------|--------|
| FAQ 阈值 | 高于此值直接返回 FAQ | 0.85 |
| Top-K 粗排 | 双重编码器召回数量 | 20-50 |
| Top-K 精排 | 交叉编码器最终返回 | 3-5 |
| 向量分数权重 | combined_score 中的权重 | 0.4 |
| 重排序分数权重 | combined_score 中的权重 | 0.6 |

### 3.5.2 性能优化

1. **模型懒加载**：避免启动时加载所有模型
2. **批量推理**：重排序时使用 batch_size
3. **缓存策略**：缓存高频问题的检索结果
4. **异步调用**：使用 httpx.AsyncClient 提高并发

### 3.5.3 质量评估

- **相关性评分**：人工标注检索结果的相关性
- **引用准确率**：检查 LLM 引用来源是否正确
- **A/B 测试**：对比不同重排序策略的效果
- **用户反馈**：收集用户对答案的满意度

---

## 3.6 工程化检查清单

- [ ] FAQ 阈值可通过配置调整
- [ ] 重排序失败时有降级方案
- [ ] 检索接口有超时控制
- [ ] 所有异常都被捕获和记录
- [ ] 引用来源信息完整（文件名、页码、评分）
- [ ] 提示词明确要求 LLM 标注来源
- [ ] 有监控指标记录检索成功率、耗时等
- [ ] 有 A/B 测试框架支持不同策略对比

---

**下一章预告**：我们将深入探讨向量检索的技术原理、混合检索架构，以及 ChromaDB 等向量数据库的使用。
