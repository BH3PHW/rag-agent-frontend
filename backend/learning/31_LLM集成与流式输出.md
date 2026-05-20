# 第4章：LLM集成与流式输出

> 🎯 **学习目标**：理解 LLM API 集成与流式输出实现
> 💡 **学习重点**：如何实现流畅的打字机效果

---

## 1. LLM集成简介

### 31.1 为什么需要流式输出

```
传统方式（非流式）：
- 等 LLM 完全生成完
- 一次性返回整个回答
- 用户需要等很久

问题：
- 等待时间长
- 用户体验差
- 感觉系统很慢

流式输出方式：
- 生成一点就返回一点
- 打字机效果
- 用户感觉很快

好处：
✅ 感知速度快
✅ 即时反馈
✅ 可中断
```

### 31.2 本项目的 LLM 选择

```
项目使用：阿里云千问（Qwen）

选择理由：
- 国内访问快
- 价格合理
- 中文效果好
- 支持流式输出
- API 稳定
```

---

## 2. 核心组件详解

### 31.1 QwenClient 客户端

```python
# 文件：backend/chat-service/llm.py

class QwenClient:
    """
    阿里云千问 API 客户端
    
    支持：
    - 非流式生成（一次性返回）
    - 流式生成（Server-Sent Events）
    """
    
    def __init__(self, api_key=None, endpoint=None, model=None):
        # 从配置读取，或使用参数
        self.api_key = api_key or settings.QWEN_API_KEY
        self.endpoint = endpoint or settings.QWEN_API_ENDPOINT
        self.model = model or settings.QWEN_MODEL
        self.temperature = settings.QWEN_TEMPERATURE
        self.max_tokens = settings.QWEN_MAX_TOKENS
```

### 31.2 非流式生成

```python
    async def generate(self, prompt, temperature=None, max_tokens=None):
        """
        非流式生成（一次性返回）
        
        适合场景：
        - 简短回答
        - 需要完整结果后处理
        - 批量处理
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "API key not configured",
                "content": "抱歉，AI服务暂时不可用。请稍后再试。"
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "success": True,
                    "content": result.get("output", {}).get("text", ""),
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "content": "抱歉，AI服务暂时不可用。"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "抱歉，服务暂时不可用。请稍后再试。"
            }
```

### 31.3 流式生成（核心）

```python
    async def generate_stream(
        self,
        prompt,
        temperature=None,
        max_tokens=None
    ):
        """
        流式生成（SSE格式）
        
        这是核心功能，实现打字机效果
        
        使用 async generator 逐步产生结果
        """
        if not self.api_key:
            yield {
                "content": "抱歉，AI服务暂时不可用。",
                "finish_reason": "stop",
                "usage": None
            }
            return
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
        
        payload = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "incremental_output": True  # 关键：启用增量输出
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    self.endpoint,
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    # 逐行处理 SSE 响应
                    async for line in response.aiter_lines():
                        line = line.strip()
                        
                        # SSE 格式：data: {...}
                        if line.startswith("data: "):
                            data_str = line[6:]
                            
                            # 结束标记
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                
                                output = data.get("output", {})
                                finish_reason = output.get("finish_reason")
                                
                                if output.get("text"):
                                    content = output.get("text", "")
                                    usage = data.get("usage")
                                    
                                    # yield 产生一个 chunk
                                    yield {
                                        "content": content,
                                        "finish_reason": finish_reason,
                                        "usage": usage
                                    }
                            except json.JSONDecodeError:
                                continue
            
        except httpx.HTTPStatusError as e:
            yield {
                "content": f"服务错误：{e.response.status_code}",
                "finish_reason": "error",
                "usage": None
            }
        except httpx.ReadTimeout:
            yield {
                "content": "抱歉，响应超时了。请稍后再试。",
                "finish_reason": "timeout",
                "usage": None
            }
        except Exception as e:
            yield {
                "content": f"抱歉，出现了一个问题：{str(e)}",
                "finish_reason": "error",
                "usage": None
            }
```

---

## 3. 流式输出的 Web 集成

### 31.1 FastAPI SSE 响应

```python
# 在 chat-service 中的使用示例
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

router = APIRouter()

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口
    返回 SSE 格式
    """
    client = get_qwen_client()
    
    async def generate():
        """
        生成器函数，包装 LLM 流式输出
        """
        prompt = build_prompt(request.messages, request.context)
        
        async for chunk in client.generate_stream(prompt):
            # 格式化为 SSE
            data = json.dumps(chunk, ensure_ascii=False)
            yield f"data: {data}\n\n"
        
        # 结束标记
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )
```

### 31.2 前端实现（打字机效果）

```javascript
// 前端 JavaScript 示例
async function streamChat(messages) {
    const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({messages})
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let result = '';
    const outputElement = document.getElementById('output');
    
    while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        // 解析 SSE 数据
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const dataStr = line.slice(6);
                
                if (dataStr === '[DONE]') {
                    return result;
                }
                
                try {
                    const data = JSON.parse(dataStr);
                    
                    if (data.content) {
                        result += data.content;
                        outputElement.textContent = result;
                        
                        // 滚动到底部
                        outputElement.scrollTop = outputElement.scrollHeight;
                    }
                } catch (e) {
                    console.error('Parse error', e);
                }
            }
        }
    }
}
```

---

## 4. 使用示例

### 31.1 非流式使用

```python
from llm import get_qwen_client

client = get_qwen_client()

# 简单调用
result = await client.generate("你好，请介绍一下自己")

if result['success']:
    print(result['content'])
    print(f"使用了 {result['tokens_used']} tokens")
else:
    print(f"错误：{result['error']}")
```

### 31.2 流式使用（基础）

```python
from llm import get_qwen_client

client = get_qwen_client()

# 流式生成
full_response = ""
async for chunk in client.generate_stream("写一首关于春天的诗"):
    if chunk['content']:
        full_response += chunk['content']
        print(chunk['content'], end='', flush=True)  # 实时输出
    
    if chunk['finish_reason'] == 'stop':
        print("\n--- 完成 ---")
        if chunk['usage']:
            print(f"Token 使用: {chunk['usage']}")

print(f"\n完整回答: {full_response}")
```

### 31.3 流式使用（带 RAG 上下文）

```python
async def rag_stream(enterprise_id, query):
    """
    完整的 RAG + 流式生成流程
    """
    # 1. 检索相关文档
    chunks = await retrieve(query, enterprise_id)
    
    # 2. 构建 Prompt
    prompt = build_rag_prompt(query, chunks)
    
    # 3. 流式生成
    client = get_qwen_client()
    
    async for chunk in client.generate_stream(prompt):
        # 可以在这里做一些处理
        # 比如：记录日志、检查内容等
        yield chunk
```

---

## 5. 工程化思维要点

### 31.1 错误处理与重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class RobustQwenClient(QwenClient):
    """
    带重试的健壮客户端
    """
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_with_retry(self, prompt):
        """
        失败自动重试
        
        策略：
        - 最多重试 3 次
        - 指数退避（2s, 4s, 8s...）
        - 只对网络错误重试
        """
        return await self.generate(prompt)
```

### 31.2 Token 计数与成本控制

```python
class CostTrackingQwenClient(QwenClient):
    """
    追踪使用量和成本
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_tokens = 0
        self.request_count = 0
    
    async def generate(self, prompt, *args, **kwargs):
        result = await super().generate(prompt, *args, **kwargs)
        
        if result['success']:
            self.total_tokens += result.get('tokens_used', 0)
            self.request_count += 1
        
        return result
    
    def get_cost_estimate(self):
        """
        估算成本
        
        假设价格：$0.01 / 1k tokens
        """
        cost = (self.total_tokens / 1000) * 0.01
        return {
            "requests": self.request_count,
            "tokens": self.total_tokens,
            "estimated_cost_usd": cost
        }
```

### 31.3 超时与取消

```python
async def generate_with_timeout(client, prompt, timeout_seconds=30):
    """
    带超时的生成
    """
    try:
        result = await asyncio.wait_for(
            client.generate(prompt),
            timeout=timeout_seconds
        )
        return result
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "Timeout",
            "content": "抱歉，响应超时了。"
        }
```

---

## 6. 产品化思维要点

### 31.1 流式输出的用户体验优化

```
优化建议：

1. 加载状态
- 显示"正在思考..."
- 给用户心理准备

2. 打字机效果控制
- 不要太快也不要太慢
- 50-100ms 每个字符比较舒适

3. 可中断
- 用户可以随时停止生成
- 释放资源

4. 错误降级
- 流式失败时，回退到非流式
- 或者给出友好提示
```

### 31.2 多模型支持

```python
from abc import ABC, abstractmethod

class LLMClient(ABC):
    """抽象基类，支持多种 LLM"""
    
    @abstractmethod
    async def generate(self, prompt):
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt):
        pass

class OpenAIClient(LLMClient):
    """OpenAI 实现"""
    ...

class QwenClient(LLMClient):
    """Qwen 实现"""
    ...

# 工厂函数
def get_llm_client(provider="qwen"):
    if provider == "openai":
        return OpenAIClient()
    elif provider == "qwen":
        return QwenClient()
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

---

## 7. 最佳实践

### 31.1 Prompt 工程

```
好的 Prompt 结构：

1. 角色设定
"你是一个专业的客服助手..."

2. 背景信息
"以下是知识库内容：
[文档片段1]
[文档片段2]
..."

3. 任务说明
"请根据以上信息回答用户问题..."

4. 输出要求
"要求：
- 准确简洁
- 不知道就说不知道
- 用中文回答"

5. 用户问题
"用户问题：{query}"
```

### 31.2 上下文窗口管理

```python
def truncate_context(messages, max_tokens=4000):
    """
    截断上下文，避免超过窗口大小
    
    策略：
    - 保留最新的消息
    - 旧消息可以截断或丢弃
    - 保留系统提示
    """
    # 估算 token 数（简单估算：1 汉字 ≈ 2 tokens）
    def estimate_tokens(text):
        return len(text) * 2
    
    result = []
    total_tokens = 0
    
    # 逆序处理，保留最新的
    for msg in reversed(messages):
        msg_tokens = estimate_tokens(msg['content'])
        
        if total_tokens + msg_tokens > max_tokens:
            break
        
        result.append(msg)
        total_tokens += msg_tokens
    
    # 恢复顺序
    return list(reversed(result))
```

---

## 8. 扩展思考

### 31.1 更高级的流式功能

```
未来可以增加：

1. 实时编辑
- 用户可以修改正在生成的内容

2. 多候选
- 同时生成多个版本
- 用户选择最好的

3. 思考过程可见
- 显示 LLM 的推理步骤
- 更透明

4. 引用来源
- 高亮显示参考了哪些文档
- 可点击跳转
```

### 31.2 本地模型部署

```
如果对延迟敏感或有隐私要求：

可选方案：
- vLLM（高性能推理）
- Text Generation Inference
- Llama.cpp（CPU 推理）

好处：
- 数据不出去
- 延迟更低
- 可控制成本

权衡：
- 需要 GPU 资源
- 部署维护复杂
```

---

## 总结：
- 流式输出是提升用户体验的关键
- 使用 async generator 实现
- SSE 是标准的 Web 推送协议
- 前端配合实现打字机效果
- 注意错误处理、重试、成本控制
