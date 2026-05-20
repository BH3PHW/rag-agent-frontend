"""
Chat Service - RAG智能客服核心服务
===================================

主要功能：
- 智能问答：基于RAG技术的AI对话回复
- 流式输出：SSE实时推送，支持打字机效果
- 敏感内容检测：关键词+语义分析双层防护
- 意图路由：FAQ优先匹配，降低LLM调用成本

核心技术：
- RAG检索增强生成：从知识库获取相关上下文
- LLM调用：集成通义千问(Qwen)大语言模型
- SSE流式：Server-Sent Events实现实时输出
"""

# 导入FastAPI核心框架
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
# SSE流式响应
from fastapi.responses import StreamingResponse
# CORS跨域支持
from fastapi.middleware.cors import CORSMiddleware
# SQLAlchemy数据库ORM
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import json

try:
    # 导入本服务配置
    from .config import settings
    # 导入数据库连接和初始化
    from .database import get_db, init_db
    # 导入Redis客户端，用于缓存和发布订阅
    from .redis_client import redis_manager
    # 导入数据模型
    from .models import ChatSession, ChatMessage
    # 导入质量评估模型
    from .quality_models import Feedback, UnmatchedQuestion
    # 导入FAQ模型
    from .faq_models import FAQ
    # 导入CRUD操作
    from . import crud
    # 导入RAG引擎
    from .rag import get_rag_engine
    # 导入敏感内容检测
    from .sensitive import detect_sensitive_content
    # 导入语义分析
    from .semantic import analyze_sensitive_meaning
    # 导入LLM客户端
    from .llm import get_qwen_client
    # 导入意图路由器
    from .intent_router import get_intent_router, IntentType, IntentDecision
    # 导入SSE流式输出器
    from .sse_stream import SSEStreamer
    # 导入防提示词注入防御
    from .prompt_injection_defender import get_prompt_injection_defender
    from .feedback_service import get_feedback_service
    # 导入Agent系统和工具
    from .agent_system import get_agent_executor
    # 导入安全验证
    from .security import get_security_service
    from .built_in_tools import set_current_security_context
    from .jwt_auth import get_jwt_service
    from .rate_limit import get_rate_limit_manager
    from .audit_logger import get_audit_logger, AuditAction, AuditSeverity
    from .api_security import (
        require_auth,
        require_permission,
        rate_limit,
        audit_log,
        Validators,
        add_security_headers
    )
    from .ecommerce_config_service import EcommerceConfigService
    # 确保模型在 init_db 之前被导入
    from . import quality_models
    from . import faq_models
    from . import ecommerce_config_models
except ImportError:
    # 直接运行时使用绝对导入
    from config import settings
    from database import get_db, init_db
    from redis_client import redis_manager
    from models import ChatSession, ChatMessage
    from quality_models import Feedback, UnmatchedQuestion
    from faq_models import FAQ
    import crud
    from rag import get_rag_engine
    from sensitive import detect_sensitive_content
    from semantic import analyze_sensitive_meaning
    from llm import get_qwen_client
    from intent_router import get_intent_router, IntentType, IntentDecision
    from sse_stream import SSEStreamer
    from prompt_injection_defender import get_prompt_injection_defender
    from feedback_service import get_feedback_service
    from agent_system import get_agent_executor
    from security import get_security_service
    from built_in_tools import set_current_security_context
    from jwt_auth import get_jwt_service
    from rate_limit import get_rate_limit_manager
    from audit_logger import get_audit_logger, AuditAction, AuditSeverity
    from api_security import (
        require_auth,
        require_permission,
        rate_limit,
        audit_log,
        Validators,
        add_security_headers
    )
    from ecommerce_config_service import EcommerceConfigService
    # 确保模型在 init_db 之前被导入
    import quality_models
    import faq_models
    import ecommerce_config_models
from pydantic import BaseModel

class AddPlatformRequest(BaseModel):
    config_schema: Optional[dict] = None

# 确保模型在 init_db 之前被导入
from . import quality_models
from . import faq_models
from . import ecommerce_config_models

# 创建FastAPI应用实例
app = FastAPI(
    title="Chat Service",
    description="RAG-powered Customer Service Chat (Stream Only)",
    version="2.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """
    健康检查端点
    用于负载均衡器和容器编排检测服务状态
    """
    return {"status": "healthy", "service": "chat-service"}


# ==================== 安全检查 ====================

async def security_check(content: str) -> dict:
    """
    防提示词注入安全检查

    检测用户输入是否包含恶意提示词注入尝试，
    如角色扮演、系统指令绕过等攻击方式

    参数:
        content: 用户输入内容

    返回:
        安全检查结果字典，包含safe布尔值和attack_type

    异常:
        HTTPException 400: 检测到不安全内容
    """
    defender = get_prompt_injection_defender()
    check_result = defender.check_content(content)

    if not check_result["safe"]:
        print(f"[SECURITY] Blocked - Type: {check_result['attack_type']}")

        raise HTTPException(
            status_code=400,
            detail={
                "error": "您的输入包含不安全内容，请重新提问。",
                "code": "UNSAFE_CONTENT",
                "security_check": check_result
            }
        )

    return check_result


# ==================== 辅助函数 ====================

async def log_unmatched_question_background(
    session_id: str,
    user_id: str,
    question: str,
    retrieval_score: float
):
    """
    异步记录相似度低的问题

    当RAG检索得分较低时，记录这个问题用于后续分析优化

    参数:
        session_id: 会话ID
        user_id: 用户ID
        question: 用户问题
        retrieval_score: 检索得分
    """
    try:
        from .database import get_db_context
        with get_db_context() as db:
            unmatched = UnmatchedQuestion(
                session_id=session_id,
                user_id=user_id,
                question=question,
                retrieval_score=retrieval_score
            )
            db.add(unmatched)
            db.commit()
            print(f"Logged low-score question: {question} (score: {retrieval_score:.2f})")
    except Exception as e:
        print(f"Error logging unmatched question: {e}")


async def create_alert_background(
    enterprise_id: str,
    alert_type: str,
    content: str,
    metadata: dict = None
):
    """
    异步创建告警

    当检测到敏感内容或其他需要人工介入的情况时，
    创建告警通知相关人员处理

    参数:
        enterprise_id: 企业ID
        alert_type: 告警类型
        content: 告警内容
        metadata: 附加元数据
    """
    try:
        from .database import get_db_context
        from .alert_models import Alert

        with get_db_context() as db:
            alert = Alert(
                enterprise_id=enterprise_id,
                alert_type=alert_type,
                content=content,
                metadata=metadata or {}
            )
            db.add(alert)
            db.commit()
            print(f"Created alert: {alert_type}")
    except Exception as e:
        print(f"Error creating alert: {e}")


# ==================== 会话管理API ====================

@app.post("/api/v1/chat/sessions")
async def create_chat_session(
    user_id: str,
    enterprise_id: str,
    title: str = None,
    db: Session = Depends(get_db)
):
    """
    创建聊天会话

    创建一个新的对话会话，用于追踪多轮对话上下文

    参数:
        user_id: 用户ID
        enterprise_id: 企业ID
        title: 会话标题（可选，自动生成）

    返回:
        新创建的会话对象
    """
    # 如果未提供标题，使用默认格式
    if not title:
        title = f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    session = ChatSession(
        user_id=user_id,
        enterprise_id=enterprise_id,
        title=title
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    print(f"Created session: {session.id} for user {user_id}")
    return session


@app.get("/api/v1/chat/sessions")
async def list_chat_sessions(
    user_id: str,
    enterprise_id: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    列出聊天会话

    获取用户的历史会话列表

    参数:
        user_id: 用户ID
        enterprise_id: 企业ID
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        会话列表
    """
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.enterprise_id == enterprise_id
    ).order_by(
        ChatSession.updated_at.desc()
    ).offset(skip).limit(limit).all()

    return sessions


@app.get("/api/v1/chat/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    获取会话详情

    获取指定会话的详细信息
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@app.delete("/api/v1/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    删除会话

    删除指定的会话及其所有消息
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 删除会话中的所有消息
    db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).delete()

    db.delete(session)
    db.commit()

    return {"message": "Session deleted"}


# ==================== 消息处理API ====================

@app.post("/api/v1/chat/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    content: str,
    user_id: str = None,
    enterprise_id: str = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    发送消息并获取AI回复（流式）

    这是核心的消息处理端点，处理流程：
    1. 安全检查 - 防提示词注入
    2. 敏感内容检测 - 关键词+语义分析
    3. 意图路由 - FAQ优先匹配
    4. RAG检索 - 获取相关上下文
    5. LLM生成 - 流式输出回复

    参数:
        session_id: 会话ID
        content: 用户消息内容
        user_id: 用户ID
        enterprise_id: 企业ID

    返回:
        SSE流式响应
    """
    # 获取会话信息
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 安全检查 - 防提示词注入
    security_result = await security_check(content)

    # 保存用户消息
    user_message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role="user",
        content=content
    )
    db.add(user_message)

    # 更新会话统计
    session.message_count += 1
    session.updated_at = datetime.utcnow()

    # 如果会话没有标题，使用第一句话作为标题
    if not session.title or session.title.startswith("会话 "):
        session.title = content[:50] + ("..." if len(content) > 50 else "")

    db.commit()

    # 预先获取历史消息 - 在流式响应生成器外部完成，减少耦合
    recent_messages = crud.get_recent_messages(db, session_id, 10)

    # 构建流式响应生成器 - 不需要直接访问数据库
    async def generate_response():
        streamer = SSEStreamer()

        try:
            # 第一步：检查敏感内容
            sensitive_result = await detect_sensitive_content(content, enterprise_id)

            if sensitive_result["is_sensitive"]:
                # 检测到敏感内容，发送警告消息
                yield streamer.event("error", {
                    "code": "SENSITIVE_CONTENT",
                    "message": "您的提问可能涉及敏感内容，建议换个话题。"
                })
                return

            # 第二步：意图路由
            intent_router = get_intent_router()
            intent = await intent_router.route(content, enterprise_id)

            if intent.intent_type == IntentType.FAQ:
                # FAQ匹配成功，直接返回FAQ答案
                yield streamer.event("message", {
                    "content": intent.faq_answer,
                    "sources": []
                })
                return

            # 第三步：RAG检索
            rag_engine = get_rag_engine()
            retrieval_result = await rag_engine.retrieve(content, enterprise_id)

            # 如果检索得分很低，记录这个问题
            if retrieval_result["score"] < 0.3 and background_tasks:
                background_tasks.add_task(
                    log_unmatched_question_background,
                    session_id, user_id, content, retrieval_result["score"]
                )

            # 第四步：LLM生成
            qwen_client = get_qwen_client()

            async for chunk in qwen_client.stream_chat(
                content=content,
                context=retrieval_result["context"],
                history=recent_messages
            ):
                yield streamer.event("chunk", {"content": chunk})

            # 发送完成信号
            yield streamer.event("done", {
                "sources": retrieval_result["sources"]
            })

        except Exception as e:
            print(f"Error in stream generation: {e}")
            yield streamer.event("error", {
                "code": "INTERNAL_ERROR",
                "message": "服务器处理出错，请稍后重试。"
            })

    # 保存助手回复（非流式，由后台任务完成）
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )


@app.get("/api/v1/chat/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    user_id: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取会话消息

    获取指定会话的历史消息列表

    参数:
        session_id: 会话ID
        user_id: 用户ID（可选，用于权限验证）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        消息列表
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(
        ChatMessage.created_at.asc()
    ).offset(skip).limit(limit).all()

    return messages


# ==================== 流式聊天API（无需会话ID） ====================

@app.post("/api/v1/chat/stream")
async def stream_chat_message(
    message: str,
    enterprise_id: str = None,
    db: Session = Depends(get_db)
):
    """
    流式聊天接口（无需预先创建会话）

    简化版的聊天接口，自动创建会话并返回流式响应
    适用于快速开始对话的场景

    参数:
        message: 用户消息内容
        enterprise_id: 企业ID（可选）

    返回:
        SSE流式响应
    """
    # 自动创建新会话
    session = ChatSession(
        user_id=None,
        enterprise_id=enterprise_id,
        title=message[:50] + ("..." if len(message) > 50 else "")
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 保存用户消息
    user_message = ChatMessage(
        session_id=session.id,
        user_id=None,
        role="user",
        content=message
    )
    db.add(user_message)
    session.message_count += 1
    db.commit()

    # 生成流式响应
    async def generate_response():
        streamer = SSEStreamer()

        try:
            # 发送会话ID
            yield streamer.event("session", {"session_id": str(session.id)})

            # 检查敏感内容
            sensitive_result = await detect_sensitive_content(message, enterprise_id)

            if sensitive_result["is_sensitive"]:
                yield streamer.event("error", {
                    "code": "SENSITIVE_CONTENT",
                    "message": "您的提问可能涉及敏感内容，建议换个话题。"
                })
                return

            # 意图路由
            intent_router = get_intent_router()
            intent = await intent_router.route(message, enterprise_id)

            if intent.intent_type == IntentType.FAQ:
                yield streamer.event("message", {
                    "content": intent.faq_answer,
                    "sources": []
                })
                return

            # RAG检索
            rag_engine = get_rag_engine()
            retrieval_result = await rag_engine.retrieve(message, enterprise_id)

            # LLM生成流式输出
            qwen_client = get_qwen_client()

            async for chunk in qwen_client.stream_chat(
                content=message,
                context=retrieval_result["context"],
                history=[]
            ):
                yield streamer.event("chunk", {"content": chunk})

            # 完成信号
            yield streamer.event("done", {
                "sources": retrieval_result["sources"]
            })

        except Exception as e:
            print(f"Stream error: {e}")
            yield streamer.event("error", {
                "code": "INTERNAL_ERROR",
                "message": "服务器处理出错，请稍后重试。"
            })

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )


# ==================== 工具调用API ====================

@app.post("/api/v1/chat/tools")
async def chat_with_tools(
    message: str,
    enterprise_id: str = None,
    user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    聊天接口（带工具调用能力）
    
    使用Agent系统进行智能工具调用，支持：
    - 订单查询
    - 商品信息
    - 知识库搜索
    - 常见问题
    - 电商平台数据
    - 人工转接

    参数:
    message: 用户消息内容
    enterprise_id: 企业ID
    user_id: 用户ID

    返回:
    工具调用结果和最终回答
    """
    security_service = get_security_service()
    
    # 验证用户身份
    security_context = security_service.validate_user_identity(
        user_id=str(user_id) if user_id else None,
        enterprise_id=str(enterprise_id) if enterprise_id else None
    )
    
    if not security_context.is_authenticated:
        return {
            "success": False,
            "error": "身份验证失败，请重新登录",
            "message": message,
            "tools_used": [],
            "tool_results": [],
            "debug_info": {"authentication": "failed"},
            "available_tools": []
        }
    
    # 设置安全上下文，供工具调用时使用
    set_current_security_context(security_context)
    
    agent_executor = get_agent_executor()
    
    # 分析并执行工具
    tools_used, results, debug_info = await agent_executor.analyze_and_execute(
        message,
        enterprise_id=str(enterprise_id) if enterprise_id else None,
        user_id=str(user_id) if user_id else None
    )
    
    # 格式化工具结果
    tool_results = []
    for r in results:
        tool_result = r["result"]
        tool_results.append({
            "tool_name": r["tool_name"],
            "success": tool_result.success,
            "data": tool_result.data,
            "error": tool_result.error_message if not tool_result.success else None
        })
    
    # 获取可用工具列表
    available_tools = []
    for tool in agent_executor.registry.list_tools():
        available_tools.append({
            "name": tool.name,
            "description": tool.description,
            "type": tool.tool_type.value if hasattr(tool.tool_type, "value") else str(tool.tool_type)
        })
    
    return {
        "success": True,
        "message": message,
        "tools_used": tools_used,
        "tool_results": tool_results,
        "debug_info": debug_info,
        "available_tools": available_tools
    }


@app.get("/api/v1/tools")
async def list_tools():
    """
    列出所有可用工具
    """
    agent_executor = get_agent_executor()
    tools = agent_executor.registry.list_tools()
    
    tool_list = []
    for tool in tools:
        tool_list.append({
            "name": tool.name,
            "description": tool.description,
            "type": tool.tool_type.value if hasattr(tool.tool_type, "value") else str(tool.tool_type),
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required
                }
                for p in tool.parameters
            ]
        })
    
    return {
        "count": len(tool_list),
        "tools": tool_list
    }


# ==================== 管理员API端点 ====================

@app.get("/api/v1/admin/sessions")
async def admin_list_sessions(
    enterprise_id: str,
    user_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    管理员查询会话列表

    供admin-service调用，返回指定企业的所有会话

    参数:
        enterprise_id: 企业ID
        user_id: 用户ID（可选，用于过滤）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        会话列表
    """
    query = db.query(ChatSession).filter(
        ChatSession.enterprise_id == enterprise_id
    )

    if user_id:
        query = query.filter(ChatSession.user_id == user_id)

    sessions = query.order_by(
        ChatSession.updated_at.desc()
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": str(s.id),
            "user_id": str(s.user_id) if s.user_id else None,
            "title": s.title,
            "message_count": s.message_count,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat()
        }
        for s in sessions
    ]


@app.get("/api/v1/admin/sessions/{session_id}")
async def admin_get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    管理员获取会话详情

    供admin-service调用，返回指定会话的详细信息

    参数:
        session_id: 会话ID

    返回:
        会话详情
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": str(session.id),
        "user_id": str(session.user_id) if session.user_id else None,
        "enterprise_id": str(session.enterprise_id),
        "title": session.title,
        "message_count": session.message_count,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }


@app.get("/api/v1/admin/sessions/{session_id}/messages")
async def admin_get_session_messages(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    管理员获取会话消息

    供admin-service调用，返回指定会话的所有消息

    参数:
        session_id: 会话ID
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        消息列表
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(
        ChatMessage.created_at.asc()
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]


@app.get("/api/v1/admin/sessions/count")
async def admin_count_sessions(
    enterprise_id: str,
    db: Session = Depends(get_db)
):
    """
    管理员统计会话数量

    供admin-service调用，返回指定企业的会话总数

    参数:
        enterprise_id: 企业ID

    返回:
        会话数量
    """
    total = db.query(ChatSession).filter(
        ChatSession.enterprise_id == enterprise_id
    ).count()

    return {"total_sessions": total}


# ==================== 反馈管理API ====================

@app.post("/api/v1/feedback")
async def submit_feedback(
    message_id: str,
    user_id: str,
    rating: str,
    reason: str = None,
    db: Session = Depends(get_db)
):
    """
    提交反馈（点赞/点踩）

    用户对AI回复进行评价，帮助优化服务质量，用于RLHF数据积累

    参数:
        message_id: 消息ID
        user_id: 用户ID
        rating: 评价类型（"thumbs_up" | "thumbs_down"）
        reason: 点踩原因（点踩时可选填）

    返回:
        反馈创建结果
    """
    feedback_service = get_feedback_service()
    
    feedback = feedback_service.create_feedback(
        message_id=message_id,
        user_id=user_id,
        rating=rating,
        reason=reason,
        db=db
    )

    return {
        "message": "Feedback submitted",
        "feedback_id": str(feedback.id),
        "rating": feedback.rating,
        "created_at": feedback.created_at.isoformat()
    }


@app.get("/api/v1/feedback/{message_id}")
async def get_message_feedback(
    message_id: str,
    db: Session = Depends(get_db)
):
    """
    获取消息的反馈

    参数:
        message_id: 消息ID

    返回:
        反馈信息
    """
    feedback_service = get_feedback_service()
    feedback = feedback_service.get_feedback(message_id, db)

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return {
        "feedback_id": str(feedback.id),
        "message_id": str(feedback.message_id),
        "user_id": str(feedback.user_id),
        "rating": feedback.rating,
        "reason": feedback.reason,
        "created_at": feedback.created_at.isoformat()
    }


@app.get("/api/v1/feedback/stats")
async def get_feedback_stats():
    """
    获取反馈统计信息

    返回:
        反馈统计数据，包括总数、点赞数、点踩数和好评率
    """
    feedback_service = get_feedback_service()
    stats = feedback_service.get_feedback_stats()

    return stats


@app.get("/api/v1/feedback/negative")
async def get_negative_feedback(limit: int = 50):
    """
    获取负面反馈列表

    获取所有点踩反馈，用于分析和优化

    参数:
        limit: 返回数量限制（默认50）

    返回:
        负面反馈列表，包含消息内容和点踩原因
    """
    feedback_service = get_feedback_service()
    negative_feedback = feedback_service.get_negative_feedback(limit=limit)

    return negative_feedback


@app.get("/api/v1/feedback/export")
async def export_feedback_for_finetuning():
    """
    导出反馈数据用于微调

    将负面反馈数据导出为RLHF格式，用于训练优化模型

    返回:
        RLHF格式的反馈数据列表
    """
    feedback_service = get_feedback_service()
    data = feedback_service.export_feedback_for_finetuning()

    return {
        "count": len(data),
        "data": data,
        "format": "rlhf"
    }


# ==================== 电商配置API ====================

@app.get("/api/v1/ecommerce/platforms")
async def get_ecommerce_platforms(enterprise_id: str):
    """
    获取企业电商平台配置

    供企业管理员调用，获取该企业已配置的电商平台列表

    参数:
        enterprise_id: 企业ID

    返回:
        电商平台配置列表
    """
    try:
        platforms = await EcommerceConfigService.get_enterprise_platforms(str(enterprise_id))
        return platforms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取平台配置失败: {str(e)}")


@app.put("/api/v1/ecommerce/platforms/{platform_id}")
async def update_ecommerce_platform(
    enterprise_id: str,
    platform_id: str,
    enabled: bool,
    api_config: Optional[dict] = None,
    sync_config: Optional[dict] = None
):
    """
    更新企业电商平台配置

    供企业管理员调用，更新指定平台的配置

    参数:
        enterprise_id: 企业ID
        platform_id: 平台ID
        enabled: 是否启用
        api_config: API配置（可选）
        sync_config: 同步配置（可选）

    返回:
        更新后的平台配置
    """
    try:
        result = await EcommerceConfigService.update_platform_config(
            enterprise_id=str(enterprise_id),
            platform_id=platform_id,
            enabled=enabled,
            api_config=api_config,
            sync_config=sync_config
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新平台配置失败: {str(e)}")


@app.get("/api/v1/ecommerce/tools")
async def get_ecommerce_tools(enterprise_id: str):
    """
    获取企业电商工具配置

    供企业管理员调用，获取该企业已配置的电商工具列表

    参数:
        enterprise_id: 企业ID

    返回:
        电商工具配置列表
    """
    try:
        tools = await EcommerceConfigService.get_tool_configs(str(enterprise_id))
        return tools
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具配置失败: {str(e)}")


@app.put("/api/v1/ecommerce/tools/{tool_name}")
async def update_ecommerce_tool(
    enterprise_id: str,
    tool_name: str,
    enabled: bool,
    config: Optional[dict] = None
):
    """
    更新企业电商工具配置

    供企业管理员调用，更新指定工具的配置

    参数:
        enterprise_id: 企业ID
        tool_name: 工具名称
        enabled: 是否启用
        config: 工具配置（可选）

    返回:
        更新后的工具配置
    """
    try:
        result = await EcommerceConfigService.update_tool_config(
            enterprise_id=str(enterprise_id),
            tool_name=tool_name,
            enabled=enabled,
            config=config
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新工具配置失败: {str(e)}")


@app.get("/api/v1/ecommerce/registry/platforms")
async def get_platform_registry():
    """
    获取平台注册表

    获取系统支持的所有电商平台列表，支持动态添加
    """
    try:
        platforms = await EcommerceConfigService.get_all_platforms()
        return platforms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取平台注册表失败: {str(e)}")


@app.post("/api/v1/ecommerce/registry/platforms")
async def add_platform(
    platform_id: str,
    name: str,
    icon: str = "🔧",
    api_type: str = "custom",
    request: Optional[AddPlatformRequest] = None
):
    """
    添加新平台

    无需重启服务，即可添加新的电商平台支持

    参数:
        platform_id: 平台唯一ID
        name: 平台名称
        icon: 平台图标（默认🔧）
        api_type: API类型（默认custom）
        request: 请求体，包含 config_schema
    """
    try:
        config_schema = request.config_schema if request else None
        result = await EcommerceConfigService.add_platform(
            platform_id=platform_id,
            name=name,
            icon=icon,
            api_type=api_type,
            config_schema=config_schema
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加平台失败: {str(e)}")


# ==================== 生命周期管理 ====================

@app.on_event("startup")
async def startup():
    """
    应用启动

    初始化数据库、Redis连接和LLM客户端
    """
    print("Chat Service starting up...")

    # 初始化数据库
    init_db()
    print("Database initialized")

    # 连接Redis
    await redis_manager.connect()
    print("Redis connected")

    # 初始化RAG引擎
    rag_engine = get_rag_engine()
    print("RAG engine initialized")

    # 初始化Agent系统（包含工具系统）
    agent_executor = get_agent_executor()
    print("Agent system initialized")

    print("Chat Service ready!")


@app.on_event("shutdown")
async def shutdown():
    """
    应用关闭

    清理资源、关闭连接
    """
    print("Chat Service shutting down...")
    await redis_manager.disconnect()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
