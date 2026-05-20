"""
API Gateway - RAG智能客服系统的统一入口
=========================================

主要功能：
- 统一API入口：接收所有前端请求，统一路由到后端微服务
- 企业隔离：确保每个企业只能访问自己的数据
- 限流保护：防止恶意请求影响系统稳定性
- 认证授权：JWT Token验证和权限检查

微服务路由：
- user-service (8001): 用户、企业、权限管理
- chat-service (8002): 智能对话、RAG检索
- knowledge-service (8003): 知识库、文档管理
- alert-service (8004): 告警通知
- channel-service (8005): 多渠道接入
"""

# 导入FastAPI核心框架和中间件
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional

# 导入HTTP客户端，用于转发请求到后端微服务
import httpx
import time
import logging
import sys
from pathlib import Path

# 添加backend根目录到Python路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

# 导入本项目的配置、安全认证和Redis客户端
try:
    from .config import settings
    from .security import (
        verify_token,
        validate_enterprise_access
    )
except ImportError:
    from config import settings
    from security import (
        verify_token,
        validate_enterprise_access
    )
try:
    from .redis_client import redis_manager
except ImportError:
    from redis_client import redis_manager

# 配置日志记录器，记录API Gateway的运行状态
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例，配置API文档信息
app = FastAPI(
    title="RAG Customer Service API Gateway",
    description="RAG智能客服系统的统一API网关，支持企业数据隔离",
    version="1.0.0"
)

# 配置CORS中间件，允许前端跨域访问
# allow_origins: 允许的源列表
# allow_credentials: 是否允许携带认证信息
# allow_methods/headers: 允许的HTTP方法和请求头
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 微服务URL配置字典
# 格式：服务名 -> 服务地址
# 通过环境变量或配置文件覆盖默认地址
SERVICES = {
    "user": settings.USER_SERVICE_URL,      # 用户服务：处理登录注册、企业管理
    "knowledge": settings.KNOWLEDGE_SERVICE_URL,  # 知识服务：文档上传、检索
    "chat": settings.CHAT_SERVICE_URL,      # 聊天服务：RAG问答、流式输出
    "alert": settings.ALERT_SERVICE_URL,    # 告警服务：敏感内容检测、通知
    "channel": settings.CHANNEL_SERVICE_URL # 渠道服务：多渠道消息接入
}

# 白名单路径：不需要认证的API端点
WHITELIST_PATHS = {
    "/",              # 根路径，返回服务信息
    "/health",        # 健康检查
    "/docs",          # API文档页面
    "/openapi.json"   # OpenAPI规范JSON
}


# ==================== 基础端点 ====================

@app.get("/")
async def root():
    """
    根路径端点
    返回API Gateway的基本信息，包括服务名称、版本和文档链接
    """
    return {
        "service": "RAG Customer Service API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "security": "Enterprise isolation enabled"
    }


@app.get("/health")
async def health_check():
    """
    健康检查端点
    用于负载均衡器和容器编排系统检测服务状态
    """
    return {"status": "healthy", "service": "api-gateway"}


# ==================== 安全认证相关 ====================

def extract_enterprise_id_from_token(token: str):
    """
    从JWT Token中提取企业ID

    参数:
        token: JWT认证令牌

    返回:
        企业ID字符串，如果Token无效则返回None
    """
    payload = verify_token(token)
    if not payload:
        return None
    return payload.get("enterprise_id")


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """
    HTTP安全中间件

    功能：
    1. 限流保护：每个IP每分钟最多100次请求
    2. 白名单豁免：白名单路径跳过限流检查

    参数:
        request: HTTP请求对象
        call_next: 下一个处理函数

    返回:
        HTTP响应对象
    """
    path = request.url.path

    # 白名单路径直接放行
    if path in WHITELIST_PATHS:
        return await call_next(request)

    # 获取客户端IP地址
    client_ip = request.client.host if request.client else "unknown"

    # 非API路径直接通过
    if not path.startswith("/api/"):
        response = await call_next(request)
        return response

    # 构建限流Redis键：格式 rate:IP:分钟时间戳
    rate_key = f"rate:{client_ip}:{int(time.time() / 60)}"

    try:
        # 连接Redis并增加请求计数
        await redis_manager.connect()
        request_count = await redis_manager.incr(rate_key)

        # 首次请求设置60秒过期时间
        if request_count == 1:
            await redis_manager.expire(rate_key, 60)

        # 超过100次/分钟触发限流
        if request_count > 100:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )
    except Exception as e:
        logger.error(f"Rate limit error: {e}")

    # 执行实际请求处理
    response = await call_next(request)
    return response


# ==================== 请求转发核心功能 ====================

async def proxy_request(
    service: str,
    path: str,
    method: str = "GET",
    params: dict = None,
    json_data: dict = None,
    headers: dict = None
):
    """
    核心请求转发函数

    将请求代理到指定的后端微服务，支持GET/POST/PUT/DELETE方法

    参数:
        service: 微服务名称(user/knowledge/chat/alert/channel)
        path: API路径，如 /api/v1/users
        method: HTTP方法，默认GET
        params: URL查询参数
        json_data: JSON请求体数据
        headers: 请求头（通常包含Authorization）

    返回:
        微服务的JSON响应

    异常:
        HTTPException: 服务不可用或返回错误状态码
    """
    # 拼接目标微服务的完整URL
    url = f"{SERVICES[service]}{path}"

    # 使用异步HTTP客户端发送请求，设置30秒超时
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 根据HTTP方法执行对应的请求
            if method == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=json_data, params=params, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=json_data, params=params, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, params=params, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

            # 检查HTTP错误状态码
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            # 后端服务返回错误状态码
            logger.error(f"HTTP error from {service}: {e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            # 后端服务不可达（网络错误、超时等）
            logger.error(f"Service {service} unavailable: {e}")
            raise HTTPException(status_code=503, detail=f"Service {service} unavailable: {str(e)}")


def get_request_headers(request: Request) -> dict:
    """
    从请求中提取认证头

    参数:
        request: FastAPI请求对象

    返回:
        包含Authorization的字典
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


async def validate_enterprise_request(request: Request, enterprise_id: str) -> str:
    """
    验证企业访问权限

    确保请求携带的Token属于目标企业，防止跨企业数据访问

    参数:
        request: HTTP请求对象
        enterprise_id: 目标企业ID

    返回:
        验证通过的企业ID

    异常:
        HTTPException 401: 未认证或Token无效
        HTTPException 403: Token中的企业ID与请求不匹配
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 从Token中提取企业ID
    token_enterprise_id = extract_enterprise_id_from_token(token)
    if not token_enterprise_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 验证企业ID匹配
    validate_enterprise_access(token_enterprise_id, enterprise_id)
    return enterprise_id


# ==================== 认证相关端点 ====================

@app.post("/api/v1/auth/register")
async def register(user: dict, request: Request):
    """
    用户注册端点

    将请求转发到user-service处理用户注册
    """
    return await proxy_request("user", "/api/v1/auth/register", "POST", json_data=user)


@app.post("/api/v1/auth/login")
async def login(login_data: dict, request: Request):
    """
    用户登录端点

    将请求转发到user-service处理用户登录，返回JWT Token
    """
    return await proxy_request("user", "/api/v1/auth/login", "POST", json_data=login_data)


@app.get("/api/v1/auth/me")
async def get_current_user(request: Request):
    """
    获取当前用户信息

    验证Token有效性后，返回当前登录用户的详细信息
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    logger.info(f"User {user_id} fetching their profile")

    return await proxy_request(
        "user",
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )


# ==================== 企业管理端点 ====================

@app.post("/api/v1/enterprises")
async def create_enterprise(data: dict, request: Request):
    """
    创建企业端点

    创建新的租户企业，每个注册用户可以创建一个企业

    请求体:
        name: 企业名称
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    logger.info(f"Creating new enterprise: {data.get('name')}")

    return await proxy_request(
        "user",
        "/api/v1/enterprises",
        "POST",
        json_data=data,
        headers={"Authorization": f"Bearer {token}"} if token else None
    )


@app.get("/api/v1/enterprises/{enterprise_id}")
async def get_enterprise(enterprise_id: str, request: Request):
    """
    获取企业详情

    获取指定企业的详细信息，包括配置、API密钥等

    参数:
        enterprise_id: 企业ID
    """
    await validate_enterprise_request(request, enterprise_id)

    logger.info(f"User accessing enterprise {enterprise_id}")

    return await proxy_request(
        "user",
        f"/api/v1/enterprises/{enterprise_id}",
        headers=get_request_headers(request)
    )


# ==================== 知识库管理端点 ====================

@app.post("/api/v1/knowledge-bases")
async def create_knowledge_base(data: dict, request: Request):
    """
    创建知识库端点

    为企业创建一个知识库，用于存储和管理文档

    请求体:
        name: 知识库名称
        enterprise_id: 企业ID
        description: 描述（可选）
    """
    enterprise_id = data.get("enterprise_id")
    if enterprise_id:
        await validate_enterprise_request(request, enterprise_id)

    logger.info(f"Creating knowledge base '{data.get('name')}' for enterprise {enterprise_id}")

    return await proxy_request(
        "knowledge",
        "/api/v1/knowledge-bases",
        "POST",
        json_data=data,
        headers=get_request_headers(request)
    )


@app.get("/api/v1/knowledge-bases")
async def list_knowledge_bases(enterprise_id: str, request: Request):
    """
    列出知识库

    获取企业下的所有知识库列表
    """
    await validate_enterprise_request(request, enterprise_id)

    logger.info(f"Listing knowledge bases for enterprise {enterprise_id}")

    return await proxy_request(
        "knowledge",
        "/api/v1/knowledge-bases",
        params={"enterprise_id": enterprise_id},
        headers=get_request_headers(request)
    )


@app.get("/api/v1/knowledge-bases/{kb_id}")
async def get_knowledge_base(kb_id: str, enterprise_id: str = None, request: Request = None):
    """
    获取知识库详情

    获取指定知识库的详细信息

    参数:
        kb_id: 知识库ID
        enterprise_id: 企业ID（可选）
    """
    if enterprise_id and request:
        await validate_enterprise_request(request, enterprise_id)

    return await proxy_request(
        "knowledge",
        f"/api/v1/knowledge-bases/{kb_id}",
        params={"enterprise_id": enterprise_id} if enterprise_id else None,
        headers=get_request_headers(request) if request else None
    )


@app.post("/api/v1/knowledge-bases/{kb_id}/documents")
async def upload_document_to_kb(
    kb_id: str,
    enterprise_id: str,
    request: Request
):
    """
    上传文档到知识库

    将文件上传到指定知识库，系统会自动进行文本提取、向量化处理

    参数:
        kb_id: 知识库ID
        enterprise_id: 企业ID
    """
    await validate_enterprise_request(request, enterprise_id)

    # 获取原始请求体（包含文件数据）
    body = await request.body()

    # 直接转发到knowledge-service，使用60秒超时处理大文件
    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {}
        token = request.headers.get("Authorization", "")
        if token:
            headers["Authorization"] = token

        response = await client.post(
            f"{SERVICES['knowledge']}/api/v1/knowledge-bases/{kb_id}/documents?enterprise_id={enterprise_id}",
            content=body,
            headers=headers
        )

        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()


@app.get("/api/v1/knowledge-bases/{kb_id}/documents")
async def list_documents_in_kb(
    kb_id: str,
    enterprise_id: str,
    request: Request
):
    """
    列出知识库中的文档

    获取指定知识库下的所有文档列表
    """
    await validate_enterprise_request(request, enterprise_id)

    return await proxy_request(
        "knowledge",
        f"/api/v1/knowledge-bases/{kb_id}/documents",
        params={"enterprise_id": enterprise_id},
        headers=get_request_headers(request)
    )


@app.delete("/api/v1/documents/{doc_id}")
async def delete_document(doc_id: str, enterprise_id: str, request: Request):
    """
    删除文档

    从知识库中删除指定的文档，同时删除对应的向量数据
    """
    await validate_enterprise_request(request, enterprise_id)

    logger.info(f"Deleting document {doc_id}")

    return await proxy_request(
        "knowledge",
        f"/api/v1/documents/{doc_id}",
        "DELETE",
        params={"enterprise_id": enterprise_id},
        headers=get_request_headers(request)
    )


@app.post("/api/v1/documents/upload")
async def upload_document(
    kb_id: str,
    enterprise_id: str,
    request: Request
):
    """
    上传文档（替代端点）

    与上一个端点功能相同，提供另一种路由方式
    """
    await validate_enterprise_request(request, enterprise_id)

    body = await request.body()

    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {}
        token = request.headers.get("Authorization", "")
        if token:
            headers["Authorization"] = token

        response = await client.post(
            f"{SERVICES['knowledge']}/api/v1/knowledge-bases/{kb_id}/documents?enterprise_id={enterprise_id}",
            content=body,
            headers=headers
        )

        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()


# ==================== 敏感词设置端点 ====================

@app.get("/api/v1/sensitive-settings")
async def get_sensitive_settings(request: Request):
    """
    获取敏感词设置

    获取企业的敏感内容检测配置，包括关键词、语义规则等
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    enterprise_id = payload.get("enterprise_id")
    if not enterprise_id:
        raise HTTPException(status_code=400, detail="Enterprise ID not found in token")

    return await proxy_request(
        "user",
        f"/api/v1/enterprises/{enterprise_id}/sensitive-settings",
        headers={"Authorization": f"Bearer {token}"}
    )


@app.put("/api/v1/sensitive-settings")
async def update_sensitive_settings(data: dict, request: Request):
    """
    更新敏感词设置

    修改企业的敏感内容检测配置
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    enterprise_id = payload.get("enterprise_id")
    if not enterprise_id:
        raise HTTPException(status_code=400, detail="Enterprise ID not found in token")

    return await proxy_request(
        "user",
        f"/api/v1/enterprises/{enterprise_id}/sensitive-settings",
        "PUT",
        json_data=data,
        headers={"Authorization": f"Bearer {token}"}
    )


@app.post("/api/v1/semantic-rules")
async def create_semantic_rule(data: dict, request: Request):
    """
    创建语义规则

    添加新的语义检测规则，用于识别特定类型的敏感内容
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    enterprise_id = payload.get("enterprise_id")
    if not enterprise_id:
        raise HTTPException(status_code=400, detail="Enterprise ID not found in token")

    return await proxy_request(
        "user",
        f"/api/v1/enterprises/{enterprise_id}/semantic-rules",
        "POST",
        json_data=data,
        headers={"Authorization": f"Bearer {token}"}
    )


@app.delete("/api/v1/semantic-rules/{rule_id}")
async def delete_semantic_rule(rule_id: str, request: Request):
    """
    删除语义规则

    移除指定的语义检测规则
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    enterprise_id = payload.get("enterprise_id")
    if not enterprise_id:
        raise HTTPException(status_code=400, detail="Enterprise ID not found in token")

    return await proxy_request(
        "user",
        f"/api/v1/enterprises/{enterprise_id}/semantic-rules/{rule_id}",
        "DELETE",
        headers={"Authorization": f"Bearer {token}"}
    )


# ==================== 聊天对话端点 ====================

@app.post("/api/v1/chat/sessions")
async def create_chat_session(data: dict, request: Request):
    """
    创建聊天会话

    创建一个新的对话会话，用于追踪多轮对话上下文
    """
    enterprise_id = data.get("enterprise_id")
    if enterprise_id:
        await validate_enterprise_request(request, enterprise_id)

    logger.info(f"Creating chat session for user {data.get('user_id')} in enterprise {enterprise_id}")

    # 提取参数作为查询参数传递
    params = {}
    if data.get("user_id"):
        params["user_id"] = str(data.get("user_id"))
    if data.get("enterprise_id"):
        params["enterprise_id"] = str(data.get("enterprise_id"))
    if data.get("title"):
        params["title"] = data.get("title")

    return await proxy_request(
        "chat",
        "/api/v1/chat/sessions",
        "POST",
        params=params,
        json_data=data,
        headers=get_request_headers(request)
    )


@app.get("/api/v1/chat/sessions")
async def list_chat_sessions(user_id: str, enterprise_id: str, request: Request):
    """
    列出聊天会话

    获取用户的所有历史对话会话
    """
    await validate_enterprise_request(request, enterprise_id)

    logger.info(f"Listing chat sessions for user {user_id} in enterprise {enterprise_id}")

    return await proxy_request(
        "chat",
        "/api/v1/chat/sessions",
        params={"user_id": user_id, "enterprise_id": enterprise_id},
        headers=get_request_headers(request)
    )


@app.post("/api/v1/chat/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    data: dict,
    request: Request
):
    """
    发送消息

    发送用户消息并获取AI回复，包含RAG检索和敏感内容检测

    参数:
        session_id: 会话ID
        data: 包含user_id, content, enterprise_id的字典
    """
    user_id = data.get("user_id")
    content = data.get("content")
    enterprise_id = data.get("enterprise_id")

    if enterprise_id:
        await validate_enterprise_request(request, enterprise_id)

    logger.info(f"User {user_id} sending message to session {session_id}")

    # 构建查询参数
    params = {}
    if user_id:
        params["user_id"] = str(user_id)
    if enterprise_id:
        params["enterprise_id"] = str(enterprise_id)
    params["content"] = content

    return await proxy_request(
        "chat",
        f"/api/v1/chat/sessions/{session_id}/messages",
        "POST",
        params=params,
        headers=get_request_headers(request)
    )


@app.get("/api/v1/chat/sessions/{session_id}/messages")
async def get_messages(session_id: str, user_id: str, enterprise_id: str = None, request: Request = None):
    """
    获取会话消息

    获取指定会话的所有历史消息
    """
    if enterprise_id and request:
        await validate_enterprise_request(request, enterprise_id)

    logger.info(f"User {user_id} fetching messages from session {session_id}")

    params = {"user_id": user_id}
    if enterprise_id:
        params["enterprise_id"] = enterprise_id

    return await proxy_request(
        "chat",
        f"/api/v1/chat/sessions/{session_id}/messages",
        params=params,
        headers=get_request_headers(request) if request else None
    )


@app.delete("/api/v1/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, user_id: str = None, request: Request = None):
    """
    删除聊天会话

    删除指定的会话，同时删除所有关联的消息记录

    参数:
        session_id: 会话ID
        user_id: 用户ID（可选，用于验证权限）
    """
    logger.info(f"Deleting chat session {session_id}")

    params = {}
    if user_id:
        params["user_id"] = user_id

    return await proxy_request(
        "chat",
        f"/api/v1/chat/sessions/{session_id}",
        "DELETE",
        params=params,
        headers=get_request_headers(request) if request else None
    )


@app.post("/api/v1/chat/stream")
async def stream_chat_message(request: Request):
    """
    流式发送聊天消息（SSE）

    使用Server-Sent Events实现流式输出，支持打字机效果

    请求体:
        message: 用户消息内容
        enterpriseId: 企业ID
    """
    try:
        body = await request.json()
        message = body.get("message")
        enterprise_id = body.get("enterpriseId")

        if not message:
            raise HTTPException(status_code=400, detail="Message content is required")

        if enterprise_id:
            await validate_enterprise_request(request, enterprise_id)

        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {}
            token = request.headers.get("Authorization", "")
            if token:
                headers["Authorization"] = token

            chat_response = await client.post(
                f"{SERVICES['chat']}/api/v1/chat/stream",
                json={"message": message, "enterprise_id": enterprise_id},
                headers=headers
            )

            if chat_response.status_code >= 400:
                raise HTTPException(
                    status_code=chat_response.status_code,
                    detail=chat_response.text
                )

            return StreamingResponse(
                chat_response.aiter_text(),
                media_type="text/event-stream",
                headers={"X-Accel-Buffering": "no"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stream chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/chat/sessions/{session_id}")
async def get_chat_session_detail(session_id: str, request: Request = None):
    """
    获取会话详情

    获取指定会话的详细信息，包括消息统计等
    """
    logger.info(f"Getting chat session detail {session_id}")

    return await proxy_request(
        "chat",
        f"/api/v1/chat/sessions/{session_id}",
        "GET",
        headers=get_request_headers(request) if request else None
    )


# ==================== 告警端点 ====================

@app.get("/api/v1/alerts")
async def list_alerts(enterprise_id: str, request: Request):
    """
    列出告警

    获取企业的所有告警列表，包括敏感内容触发、人工转接等
    """
    await validate_enterprise_request(request, enterprise_id)

    logger.info(f"Listing alerts for enterprise {enterprise_id}")

    return await proxy_request(
        "alert",
        "/api/v1/alerts",
        params={"enterprise_id": enterprise_id},
        headers=get_request_headers(request)
    )


@app.put("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: Request):
    """
    确认告警

    将告警标记为已处理状态
    """
    logger.info(f"Acknowledging alert {alert_id}")

    return await proxy_request(
        "alert",
        f"/api/v1/alerts/{alert_id}/acknowledge",
        "PUT",
        headers=get_request_headers(request)
    )


@app.put("/api/v1/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    data: dict = None,
    request: Request = None
):
    """
    解决告警

    将告警标记为已解决，可以附加处理说明
    """
    logger.info(f"Resolving alert {alert_id}")

    return await proxy_request(
        "alert",
        f"/api/v1/alerts/{alert_id}/resolve",
        "PUT",
        json_data=data,
        headers=get_request_headers(request) if request else None
    )


# ==================== 渠道服务端点 ====================

@app.post("/api/v1/channel/{enterprise_id}/{platform_type}/webhook")
async def channel_webhook(
    enterprise_id: str,
    platform_type: str,
    request: Request
):
    """
    接收渠道Webhook

    接收来自微信公众号、钉钉等渠道的消息回调

    参数:
        enterprise_id: 企业ID
        platform_type: 平台类型（wechat/dingtalk/feishu等）
    """
    body = await request.body()
    content_type = request.headers.get("content-type", "")

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {}
        if content_type:
            headers["content-type"] = content_type

        response = await client.post(
            f"{SERVICES['channel']}/api/v1/channel/{enterprise_id}/{platform_type}/webhook",
            content=body,
            headers=headers
        )
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.post("/api/v1/channel/{enterprise_id}/message")
async def send_channel_message(
    enterprise_id: str,
    request: Request
):
    """
    通过渠道发送消息

    使用统一格式通过各渠道发送消息
    """
    data = await request.json()
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/message",
        "POST",
        json_data=data
    )


@app.get("/api/v1/channel/{enterprise_id}/oneid/mappings")
async def get_oneid_mappings(
    enterprise_id: str,
    unified_user_id: str,
    request: Request = None
):
    """
    获取用户映射

    获取统一用户ID在各渠道的映射关系
    """
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/oneid/mappings",
        "GET",
        params={"unified_user_id": unified_user_id},
        headers=get_request_headers(request) if request else None
    )


@app.post("/api/v1/channel/{enterprise_id}/oneid/link-phone")
async def link_oneid_phone(
    enterprise_id: str,
    request: Request
):
    """
    绑定手机号

    将用户手机号与统一ID关联
    """
    data = await request.json()
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/oneid/link-phone",
        "POST",
        json_data=data
    )


@app.post("/api/v1/channel/{enterprise_id}/oneid/link-crm")
async def link_oneid_crm(
    enterprise_id: str,
    request: Request
):
    """
    绑定CRM ID

    将CRM系统中的客户ID与统一ID关联
    """
    data = await request.json()
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/oneid/link-crm",
        "POST",
        json_data=data
    )


@app.post("/api/v1/channel/{enterprise_id}/config")
async def set_channel_config(
    enterprise_id: str,
    request: Request
):
    """
    设置渠道配置

    配置企业各渠道的接入参数
    """
    data = await request.json()
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/config",
        "POST",
        json_data=data
    )


@app.get("/api/v1/channel/{enterprise_id}/configs")
async def get_channel_configs(
    enterprise_id: str,
    request: Request = None
):
    """
    获取渠道配置列表

    获取企业的所有渠道配置
    """
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/configs",
        "GET",
        headers=get_request_headers(request) if request else None
    )


# ==================== 渠道账户管理API ====================

@app.get("/api/v1/channel/{enterprise_id}/accounts")
async def list_channel_accounts(
    enterprise_id: str,
    channel_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    request: Request = None
):
    """
    列出渠道账户

    获取企业的所有渠道账户，支持按类型和状态筛选

    参数:
        enterprise_id: 企业ID
        channel_type: 渠道类型筛选（可选）
        status: 状态筛选（可选）
        skip: 跳过记录数（分页）
        limit: 返回记录数限制
    """
    params = {"enterprise_id": enterprise_id}
    if channel_type:
        params["channel_type"] = channel_type
    if status:
        params["status"] = status
    params["skip"] = skip
    params["limit"] = limit

    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/accounts",
        "GET",
        params=params,
        headers=get_request_headers(request) if request else None
    )


@app.get("/api/v1/channel/{enterprise_id}/accounts/{account_id}")
async def get_channel_account(
    enterprise_id: str,
    account_id: str,
    request: Request = None
):
    """
    获取渠道账户详情

    获取单个渠道账户的详细信息
    """
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/accounts/{account_id}",
        "GET",
        headers=get_request_headers(request) if request else None
    )


@app.post("/api/v1/channel/{enterprise_id}/accounts")
async def create_channel_account(
    enterprise_id: str,
    request: Request
):
    """
    创建渠道账户

    为企业添加新的渠道接入账户
    """
    data = await request.json()
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/accounts",
        "POST",
        json_data=data,
        headers=get_request_headers(request)
    )


@app.put("/api/v1/channel/{enterprise_id}/accounts/{account_id}")
async def update_channel_account(
    enterprise_id: str,
    account_id: str,
    request: Request
):
    """
    更新渠道账户

    修改渠道账户的配置信息
    """
    data = await request.json()
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/accounts/{account_id}",
        "PUT",
        json_data=data,
        headers=get_request_headers(request)
    )


@app.post("/api/v1/channel/{enterprise_id}/accounts/{account_id}/activate")
async def activate_channel_account(
    enterprise_id: str,
    account_id: str,
    request: Request = None
):
    """
    激活渠道账户

    启用指定渠道账户的接入功能
    """
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/accounts/{account_id}/activate",
        "POST",
        headers=get_request_headers(request) if request else None
    )


@app.post("/api/v1/channel/{enterprise_id}/accounts/{account_id}/deactivate")
async def deactivate_channel_account(
    enterprise_id: str,
    account_id: str,
    request: Request = None
):
    """
    停用渠道账户

    暂停指定渠道账户的接入功能
    """
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/accounts/{account_id}/deactivate",
        "POST",
        headers=get_request_headers(request) if request else None
    )


@app.delete("/api/v1/channel/{enterprise_id}/accounts/{account_id}")
async def delete_channel_account(
    enterprise_id: str,
    account_id: str,
    request: Request = None
):
    """
    删除渠道账户

    永久删除指定的渠道账户
    """
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/accounts/{account_id}",
        "DELETE",
        headers=get_request_headers(request) if request else None
    )


@app.get("/api/v1/channel/{enterprise_id}/accounts/{account_id}/logs")
async def get_channel_access_logs(
    enterprise_id: str,
    account_id: str,
    log_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    request: Request = None
):
    """
    获取渠道接入日志

    查看渠道账户的消息收发记录和错误日志
    """
    params = {}
    if log_type:
        params["log_type"] = log_type
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    params["skip"] = skip
    params["limit"] = limit

    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/accounts/{account_id}/logs",
        "GET",
        params=params,
        headers=get_request_headers(request) if request else None
    )


@app.post("/api/v1/channel/{enterprise_id}/accounts/{account_id}/test")
async def test_channel_connection(
    enterprise_id: str,
    account_id: str,
    request: Request = None
):
    """
    测试渠道连接

    验证渠道账户的连接配置是否正确
    """
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/accounts/{account_id}/test",
        "POST",
        headers=get_request_headers(request) if request else None
    )


@app.get("/api/v1/channel/{enterprise_id}/stats/overview")
async def get_channel_stats(
    enterprise_id: str,
    request: Request = None
):
    """
    获取渠道统计概览

    获取企业在各渠道的消息统计，包括收发数量、成功率等
    """
    return await proxy_request(
        "channel",
        f"/api/v1/channel/{enterprise_id}/stats/overview",
        "GET",
        headers=get_request_headers(request) if request else None
    )


@app.get("/api/v1/channel/platforms")
async def get_supported_platforms():
    """
    获取支持的平台列表

    返回系统支持的所有渠道平台及其配置说明
    """
    return await proxy_request(
        "channel",
        "/api/v1/channel/platforms",
        "GET"
    )


# ==================== 生命周期管理 ====================

@app.on_event("startup")
async def startup():
    """
    应用启动事件

    初始化Redis连接，建立连接池
    """
    print("API Gateway starting up...")
    print("Security features: Enterprise isolation enabled")
    try:
        await redis_manager.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")


@app.on_event("shutdown")
async def shutdown():
    """
    应用关闭事件

    关闭Redis连接，清理资源
    """
    print("API Gateway shutting down...")
    await redis_manager.disconnect()
