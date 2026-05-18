# 流式输出 (SSE) 实现文档

## 概述

本实现通过 Server-Sent Events (SSE) 技术为聊天接口提供流式输出功能，显著降低用户等待时间，提升聊天体验。

## 功能特性

- 实时流式输出：LLM 生成的内容逐块推送给前端
- 完整支持意图路由：FAQ 匹配、闲聊回复、转人工等不走 LLM 的场景也能流式返回
- 消息持久化：流式输出结束后自动保存完整回复到数据库
- 错误处理：优雅处理超时、网络错误等异常情况
- 向后兼容：原有一次性返回接口保持不变

## 新增/修改文件

| 文件 | 说明 |
|------|------|
| `chat-service/llm.py` | 新增 `generate_stream` 方法，支持流式调用 Qwen API |
| `chat-service/sse_stream.py` | SSE 流式输出核心模块 |
| `chat-service/main.py` | 新增 `/api/v1/chat/sessions/{session_id}/messages/stream` 接口 |

## API 使用

### 流式聊天接口

**端点**: `POST /api/v1/chat/sessions/{session_id}/messages/stream`

**请求参数**:
- `content`: 消息内容 (必填)
- `user_id`: 用户 ID (必填)
- `enterprise_id`: 企业 ID (必填)

**响应**: SSE 流式响应

### SSE 事件格式

#### 1. start 事件
```js
data: {
  "type": "start",
  "timestamp": "2024-01-15T10:30:00.123Z",
  "intent": "rag",
  "cost_tier": "HIGH",
  "user_message_id": "550e8400-..."
}
```

#### 2. content 事件 (多次)
```js
data: {
  "type": "content",
  "content": "你好，",
  "finish_reason": null
}
data: {
  "type": "content",
  "content": "我是智能客服。",
  "finish_reason": null
}
```

#### 3. end 事件
```js
data: {
  "type": "end",
  "finish_reason": "stop",
  "full_content": "你好，我是智能客服。",
  "usage": { "total_tokens": 150 },
  "timestamp": "2024-01-15T10:30:02.456Z"
}
```

#### 4. error 事件 (出错时)
```js
data: {
  "type": "error",
  "error": "服务错误：500",
  "code": "SERVICE_ERROR"
}
```

## 前端实现示例

### 原生 JavaScript

```javascript
async function sendStreamMessage(sessionId, content, userId, enterpriseId) {
  const response = await fetch(
    `http://localhost:8080/api/v1/chat/sessions/${sessionId}/messages/stream`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content,
        user_id: userId,
        enterprise_id: enterpriseId
      })
    }
  );

  if (!response.ok) {
    throw new Error('请求失败');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullText = '';

  try {
    while (true) {
      const { value, done } = await reader.read();
      
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            handleStreamEvent(data);
          } catch (e) {
            console.error('解析 SSE 数据失败:', e);
          }
        }
      }
    }
  } catch (e) {
    console.error('流式接收失败:', e);
  }

  function handleStreamEvent(data) {
    switch (data.type) {
      case 'start':
        console.log('开始接收，意图:', data.intent);
        break;
        
      case 'content':
        fullText += data.content;
        updateChatMessage(fullText);
        break;
        
      case 'end':
        console.log('结束，Token 使用:', data.usage?.total_tokens);
        break;
        
      case 'error':
        console.error('错误:', data.error);
        break;
    }
  }
}

function updateChatMessage(text) {
  // 更新聊天界面中的消息
  const messageEl = document.getElementById('current-message');
  messageEl.textContent = text;
}
```

### 使用 EventSource (简化版)

```javascript
// 注意: EventSource 只支持 GET 请求，需要适配后端
const eventSource = new EventSource(
  `http://localhost:8080/api/v1/chat/sessions/${sessionId}/messages/stream?content=你好`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到数据:', data);
};

eventSource.onerror = (e) => {
  console.error('SSE 错误:', e);
  eventSource.close();
};
```

## 后端架构

### 1. LLM 客户端扩展 (`llm.py`)

```python
async def generate_stream(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
    """流式生成，返回异步迭代器"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST", self.endpoint,
            headers=headers,
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    # 解析并 yield 每一块
                    yield parse_line(line)
```

### 2. SSE 格式化 (`sse_stream.py`)

提供的工具方法：
- `format_event()`: 格式化单个 SSE 事件
- `generate_sse_stream()`: 完整流式生成管道
- `generate_simple_response()`: 非 LLM 场景的简单流式响应
- `generate_error_response()`: 错误响应

### 3. 流式接口 (`main.py`)

`send_message_stream` 处理流程：

1. 验证会话
2. 保存用户消息
3. 意图路由识别
4. 根据不同情况返回对应流式响应：
   - 闲聊/FAQ: `generate_simple_response()`
   - 错误: `generate_error_response()`
   - LLM: 完整 `generate_sse_stream()` + 数据库保存

## 性能优化

- 流式传输降低首字节响应时间 (TTFB)
- 消息立即保存到数据库，提升用户感知
- 大回复可以边生成边展示，不用等完整返回

## 错误处理

- **LLM 超时**: 返回 timeout 结束事件
- **网络错误**: 记录日志 + 返回错误事件
- **数据库失败**: 回滚事务，错误响应

## 兼容性

- 保持原有非流式接口不变
- 新的流式接口提供更好的体验
- 两者可以并存，前端按需要选择

## 测试方法

### 使用 curl 测试

```bash
curl -N -X POST "http://localhost:8080/api/v1/chat/sessions/550e8400/messages/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好",
    "user_id": "550e8400",
    "enterprise_id": "550e8400"
  }'
```

### 使用 Node.js 测试

```javascript
const fetch = require('node-fetch');

async function testStream() {
  const res = await fetch('http://localhost:8080/.../stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ /* ... */ })
  });
  
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    console.log(decoder.decode(value));
  }
}

testStream();
```
