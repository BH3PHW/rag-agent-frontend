# 第8章：FastAPI 核心使用与工程化实践

> 🎯 **学习目标**：掌握FastAPI核心使用，理解工程化开发思维
> 💡 **工程化思维**：代码可维护、可测试、可部署、可扩展
> 💡 **产品化思维**：用户体验、性能优化、安全保障

---

## 16.1 为什么选择FastAPI？

### 16.1.1 技术选型对比

| 框架 | 性能 | 开发效率 | 类型安全 | 自动文档 | 异步支持 | 学习曲线 |
|------|------|---------|---------|---------|---------|---------|
| FastAPI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中等 |
| Django | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 陡 |
| Flask | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | 平缓 |
| Starlette | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中等 |

### 16.1.2 工程化优势

**产品化思维**：为什么FastAPI适合做产品？

```
用户端视角：
┌────────────────────────────────────────────────────────────┐
│  1. 快速响应 - 高性能异步架构，延迟低                       │
│  2. 稳定可靠 - 强类型检查，运行时错误少                     │
│  3. 功能完整 - 自动生成API文档，方便联调                   │
└────────────────────────────────────────────────────────────┘

开发端视角：
┌────────────────────────────────────────────────────────────┐
│  1. 类型安全 - Pydantic自动验证，减少bug                   │
│  2. 调试方便 - 自动文档 + 交互式API测试界面                │
│  3. 现代标准 - 支持OpenAPI 3.0，生态完善                   │
└────────────────────────────────────────────────────────────┘
```

---

## 16.2 FastAPI 核心概念

### 16.2.1 应用初始化与配置

```python
# 文件：backend/api-gateway/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseSettings

# 工程化：集中配置管理
class Settings(BaseSettings):
    """统一配置管理"""
    app_name: str = "RAG智能客服API网关"
    debug: bool = False
    
    # 服务地址配置
    user_service_url: str = "http://localhost:8001"
    chat_service_url: str = "http://localhost:8002"
    knowledge_service_url: str = "http://localhost:8003"
    
    # 安全配置
    secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    
    class Config:
        env_file = ".env"
        env_prefix = "RAG_"  # 环境变量前缀

settings = Settings()

# 工程化：应用初始化，集中管理生命周期
def create_app() -> FastAPI:
    """应用工厂模式 - 方便测试和扩展"""
    
    app = FastAPI(
        title=settings.app_name,
        description="RAG智能客服系统API网关",
        version="1.0.0",
        docs_url="/docs",        # Swagger文档
        redoc_url="/redoc",      # ReDoc文档
        openapi_url="/openapi.json"
    )
    
    # 工程化：配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境需限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 工程化：健康检查端点（监控需要）
    @app.get("/health")
    async def health_check():
        """健康检查端点 - 监控系统调用"""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "gateway": "ok"
            }
        }
    
    # 工程化：路由注册集中管理
    from .routes import auth, chat, knowledge
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.include_router(chat.router, prefix="/api/v1/chat")
    app.include_router(knowledge.router, prefix="/api/v1/knowledge")
    
    return app

app = create_app()

# 工程化：启动日志
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
```

### 16.2.2 Pydantic - 类型安全与数据验证

**工程化思维**：为什么要重视数据验证？

```
数据验证的价值：
┌────────────────────────────────────────────────────────────┐
│  1. 提升安全性 - 防止SQL注入、XSS等攻击                     │
│  2. 提升稳定性 - 提前发现类型错误，减少线上bug             │
│  3. 提升开发效率 - 自动生成文档，减少调试时间               │
│  4. 提升可维护性 - 数据模型清晰，容易理解和修改             │
└────────────────────────────────────────────────────────────┘
```

**代码示例**：

```python
# 文件：backend/api-gateway/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# 工程化：清晰的请求/响应模型
class ChatRequest(BaseModel):
    """聊天请求模型"""
    query: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    session_id: Optional[str] = Field(None, description="会话ID")
    knowledge_base_ids: Optional[List[str]] = Field(None, description="指定知识库")
    stream: bool = Field(default=True, description="是否流式返回")
    
    # 工程化：自定义验证器
    @validator('query')
    def validate_query_content(cls, v: str) -> str:
        """验证问题内容 - 产品化：内容安全"""
        v = v.strip()
        if len(v) == 0:
            raise ValueError("问题不能为空")
        
        # 产品化：敏感词检测
        forbidden_words = ["敏感词1", "敏感词2"]
        for word in forbidden_words:
            if word in v:
                raise ValueError("问题包含不合适内容")
        return v

class ChatMessageResponse(BaseModel):
    """聊天消息响应模型"""
    message_id: str
    role: str = Field(..., description="角色：user或assistant")
    content: str
    timestamp: datetime
    sources: Optional[List[dict]] = Field(None, description="引用来源")
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": "msg_123",
                "role": "assistant",
                "content": "根据我们的政策...",
                "timestamp": "2024-01-15T10:30:00",
                "sources": [{"source": "FAQ", "score": 0.92}]
            }
        }
```

---

## 16.3 路由与依赖注入 - 工程化实践

### 16.3.1 路由组织

**工程化思维**：如何组织路由让代码更易维护？

```
推荐的路由结构：
┌────────────────────────────────────────────────────────────┐
│  backend/                                                   │
│    └── api-gateway/                                         │
│         ├── main.py              # 应用入口                │
│         ├── routes/              # 路由目录               │
│         │    ├── __init__.py                              │
│         │    ├── auth.py           # 认证路由             │
│         │    ├── chat.py           # 聊天路由             │
│         │    └── knowledge.py      # 知识库路由           │
│         ├── deps.py              # 依赖注入              │
│         ├── schemas.py           # 数据模型              │
│         └── services/            # 业务逻辑服务         │
└────────────────────────────────────────────────────────────┘
```

**代码示例**：

```python
# 文件：backend/api-gateway/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException
from ..schemas import ChatRequest, ChatMessageResponse, ChatSessionResponse
from ..deps import get_current_user, validate_token
from ..services.chat_service import ChatService

router = APIRouter(tags=["聊天"])

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    enterprise_id: str = Depends(validate_token),
    chat_service: ChatService = Depends()
):
    """
    创建聊天会话
    
    产品化：
    - 自动关联企业ID，多租户隔离
    - 会话记录用于后续统计和分析
    - 支持会话复用，提升用户体验
    """
    try:
        session = await chat_service.create_session(
            enterprise_id=enterprise_id
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    request: ChatRequest,
    enterprise_id: str = Depends(validate_token)
):
    """发送消息 - 非流式版本"""
    chat_service = ChatService()
    response = await chat_service.send_message(
        session_id=session_id,
        query=request.query,
        enterprise_id=enterprise_id
    )
    return response
```

### 16.3.2 依赖注入 - 安全与复用

```python
# 文件：backend/api-gateway/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import ValidationError

security = HTTPBearer()

async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Token验证依赖
    
    工程化：
    - 统一的认证逻辑，避免重复代码
    - 可复用的依赖注入
    - 清晰的错误处理
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        enterprise_id: str = payload.get("enterprise_id")
        if enterprise_id is None:
            raise credentials_exception
        
        return enterprise_id
        
    except (JWTError, ValidationError):
        raise credentials_exception
```

---

## 16.4 流式响应 - 产品化体验

### 16.4.1 为什么需要流式响应？

**产品化思维**：用户体验是产品成功的关键

```
传统同步响应 vs 流式响应对比：
┌─────────────────────────────────────────────────────────────┐
│  传统方式（同步）：                                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  用户输入 → 等待LLM生成 → 等待完整回答 → 显示完整回答  │  │
│  │  ↓ 总耗时：10秒+ → 用户体验差，容易流失              │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  流式响应方式：                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  用户输入 → 立即开始打字机效果 → 边生成边显示        │  │
│  │  ↓ 用户感觉很快，体验大幅提升                        │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 16.4.2 SSE 流式实现

```python
# 文件：backend/chat-service/routes.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

router = APIRouter(tags=["聊天"])

class SSEStreamer:
    """SSE流式响应工具 - 工程化：统一工具类"""
    
    @staticmethod
    def event(event_type: str, data: dict) -> str:
        """生成SSE格式事件"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

@router.post("/sessions/{session_id}/messages/stream")
async def stream_chat_message(
    session_id: str,
    query: str,
    enterprise_id: str
):
    """
    流式聊天端点 - 产品化：打字机效果
    
    工程化：
    - 统一的流式响应格式
    - 包含进度、错误、完成等事件类型
    - 前端可以统一处理
    """
    async def generate():
        streamer = SSEStreamer()
        
        # 工程化：发送开始事件
        yield streamer.event("start", {
            "session_id": session_id,
            "status": "generating"
        })
        
        try:
            # 调用LLM获取流式响应
            llm = LLMService()
            async for chunk in llm.stream_generate(query):
                # 工程化：发送内容块
                yield streamer.event("message", {
                    "type": "chunk",
                    "content": chunk
                })
            
            # 工程化：发送完成事件
            yield streamer.event("done", {
                "type": "complete",
                "sources": []
            })
            
        except Exception as e:
            # 工程化：错误处理
            yield streamer.event("error", {
                "type": "error",
                "message": str(e)
            })
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

---

## 16.5 中间件 - 横切关注点

### 16.5.1 日志中间件

```python
# 文件：backend/api-gateway/middleware.py
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# 工程化：结构化日志
logger = logging.getLogger("api-gateway")

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    工程化价值：
    - 性能监控：记录响应时间
    - 问题排查：记录请求详情
    - 安全审计：记录访问日志
    """
    
    async def dispatch(self, request: Request, call_next):
        # 记录开始时间
        start_time = time.time()
        
        # 工程化：记录请求信息
        logger.info(
            f"Request: {request.method} {request.url.path}, "
            f"Client: {request.client.host}"
        )
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 工程化：记录响应信息
            logger.info(
                f"Response: {request.method} {request.url.path}, "
                f"Status: {response.status_code}, "
                f"Duration: {process_time:.3f}s"
            )
            
            # 工程化：添加响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 工程化：异常记录
            process_time = time.time() - start_time
            logger.error(
                f"Error processing request: {request.method} {request.url.path}, "
                f"Error: {str(e)}, Duration: {process_time:.3f}s"
            )
            raise
```

### 16.5.2 限流中间件

```python
from fastapi import HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 工程化：限流配置
limiter = Limiter(key_func=get_remote_address)

# 使用示例
@router.post("/chat")
@limiter.limit("60/minute")  # 每分钟最多60次
async def chat(request: Request):
    """聊天端点 - 限流保护"""
    # 处理逻辑...
    pass
```

---

## 16.6 工程化最佳实践

### 16.6.1 分层架构

```
清晰的分层架构 - 可维护性的基础：
┌────────────────────────────────────────────────────────────┐
│  API层（routes）：                                           │
│  - HTTP请求/响应处理                                        │
│  - 参数验证                                                │
│  - 调用业务逻辑层                                           │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  业务逻辑层（services）：                                    │
│  - 核心业务逻辑                                             │
│  - 数据处理                                                 │
│  - 不感知HTTP                                              │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  数据访问层（db）：                                          │
│  - 数据库操作                                               │
│  - 不感知业务逻辑                                           │
└────────────────────────────────────────────────────────────┘
```

### 16.6.2 测试支持

```python
# 文件：backend/chat-service/tests/test_chat.py
import pytest
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

# 工程化：测试用例
def test_create_session():
    """测试创建会话"""
    response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data

def test_send_message():
    """测试发送消息"""
    # 先创建会话
    session_resp = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": "Bearer test-token"}
    )
    session_id = session_resp.json()["session_id"]
    
    # 发送消息
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "query": "你好",
            "stream": False
        },
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
```

---

## 16.7 本章小结

### 核心概念

| 概念 | 工程化价值 |
|------|-----------|
| **Pydantic** | 类型安全，数据验证，自动文档 |
| **依赖注入** | 代码复用，逻辑清晰，易于测试 |
| **中间件** | 横切关注点（日志、限流、认证） |
| **流式响应** | 产品体验，用户满意度 |
| **分层架构** | 可维护，可测试，可扩展 |

### 工程化思维要点

1. **配置集中管理** - Settings类统一管理
2. **数据验证前置** - Pydantic模型验证输入
3. **分层清晰** - API、业务、数据分离
4. **中间件封装** - 横切关注点统一处理
5. **日志完善** - 问题排查、性能监控
6. **测试先行** - 保证代码质量

### 产品化思维要点

1. **用户体验** - 流式响应、快速反馈
2. **数据安全** - 验证、权限、限流
3. **稳定可靠** - 异常处理、监控
4. **可扩展** - 预留扩展接口

### 下一步学习

- [32_Redis缓存使用.md](./32_Redis缓存使用.md) - Redis在项目中的应用
