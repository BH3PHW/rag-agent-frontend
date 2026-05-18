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

# 确保模型在 init_db 之前被导入
from . import quality_models
from . import faq_models

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
    session_id: UUID,
    user_id: UUID,
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
    enterprise_id: UUID,
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
    user_id: UUID,
    enterprise_id: UUID,
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
    user_id: UUID,
    enterprise_id: UUID,
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
    session_id: UUID,
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
    session_id: UUID,
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
    session_id: UUID,
    content: str,
    user_id: UUID = None,
    enterprise_id: UUID = None,
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

    # 构建流式响应生成器
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
            if retrieval_result["score"] < 0.3:
                background_tasks.add_task(
                    log_unmatched_question_background,
                    session_id, user_id, content, retrieval_result["score"]
                )

            # 第四步：LLM生成
            qwen_client = get_qwen_client()

            async for chunk in qwen_client.stream_chat(
                content=content,
                context=retrieval_result["context"],
                history=self.get_recent_messages(session_id, db)
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
    session_id: UUID,
    user_id: UUID = None,
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
    enterprise_id: UUID = None,
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


# ==================== 反馈管理API ====================

@app.post("/api/v1/feedback")
async def submit_feedback(
    message_id: UUID,
    user_id: UUID,
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
    message_id: UUID,
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

    print("Chat Service ready!")


@app.on_event("shutdown")
async def shutdown():
    """
    应用关闭

    清理资源、关闭连接
    """
    print("Chat Service shutting down...")
    await redis_manager.disconnect()
