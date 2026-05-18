"""
Analytics Service - Main Application
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import json

from .config import settings
from .database import get_db, init_db
from .models import MessageFeedback, QueryLog, ConversationArchive, HotQuery, MissedQuery
from .redis_client import redis_manager


app = FastAPI(
    title="Analytics Service",
    description="Data Analytics and Insights Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics-service"}


# ============ 反馈管理 ============

@app.post("/api/v1/feedback")
async def submit_feedback(
    message_id: UUID,
    session_id: UUID,
    user_id: UUID,
    enterprise_id: UUID,
    rating: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    提交消息反馈
    - rating: "thumbs_up" | "thumbs_down"
    - reason: 点踩时必须填写原因
    """
    if rating not in ["thumbs_up", "thumbs_down"]:
        raise HTTPException(status_code=400, detail="Invalid rating value")

    if rating == "thumbs_down" and not reason:
        raise HTTPException(status_code=400, detail="Reason is required for negative feedback")

    feedback = MessageFeedback(
        message_id=message_id,
        session_id=session_id,
        user_id=user_id,
        enterprise_id=enterprise_id,
        rating=rating,
        reason=reason
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "id": str(feedback.id),
        "rating": feedback.rating,
        "created_at": feedback.created_at.isoformat()
    }


@app.get("/api/v1/feedback")
async def list_feedback(
    enterprise_id: UUID,
    rating: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取反馈列表"""
    query = db.query(MessageFeedback).filter(MessageFeedback.enterprise_id == enterprise_id)

    if rating:
        query = query.filter(MessageFeedback.rating == rating)
    if start_date:
        query = query.filter(MessageFeedback.created_at >= start_date)
    if end_date:
        query = query.filter(MessageFeedback.created_at <= end_date)

    feedbacks = query.order_by(MessageFeedback.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": str(f.id),
            "message_id": str(f.message_id),
            "rating": f.rating,
            "reason": f.reason,
            "created_at": f.created_at.isoformat()
        }
        for f in feedbacks
    ]


@app.get("/api/v1/feedback/stats")
async def get_feedback_stats(
    enterprise_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """获取反馈统计"""
    query = db.query(MessageFeedback).filter(MessageFeedback.enterprise_id == enterprise_id)

    if start_date:
        query = query.filter(MessageFeedback.created_at >= start_date)
    if end_date:
        query = query.filter(MessageFeedback.created_at <= end_date)

    total = query.count()
    positive = query.filter(MessageFeedback.rating == "thumbs_up").count()
    negative = query.filter(MessageFeedback.rating == "thumbs_down").count()

    negative_with_reasons = db.query(
        MessageFeedback.reason,
        func.count(MessageFeedback.id).label('count')
    ).filter(
        MessageFeedback.enterprise_id == enterprise_id,
        MessageFeedback.rating == "thumbs_down"
    ).group_by(MessageFeedback.reason).order_by(desc('count')).limit(10).all()

    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_rate": round(positive / total * 100, 2) if total > 0 else 0,
        "negative_reasons": [{"reason": r, "count": c} for r, c in negative_with_reasons]
    }


# ============ 查询埋点 ============

@app.post("/api/v1/query-logs")
async def log_query(
    session_id: UUID,
    user_id: UUID,
    enterprise_id: UUID,
    query: str,
    response_type: str,
    retrieval_score: Optional[float] = None,
    tokens_used: int = 0,
    response_time_ms: int = 0,
    sources_count: int = 0,
    db: Session = Depends(get_db)
):
    """
    记录查询日志
    - response_type: "faq" | "rag" | "rule" | "human"
    """
    is_miss = retrieval_score is not None and retrieval_score < 0.5

    query_log = QueryLog(
        session_id=session_id,
        user_id=user_id,
        enterprise_id=enterprise_id,
        query=query,
        response_type=response_type,
        retrieval_score=retrieval_score,
        is_miss=is_miss,
        tokens_used=tokens_used,
        response_time_ms=response_time_ms,
        sources_count=sources_count
    )
    db.add(query_log)

    # 更新热词统计
    normalized_query = query.lower().strip()
    hot_query = db.query(HotQuery).filter(
        HotQuery.enterprise_id == enterprise_id,
        HotQuery.query_normalized == normalized_query
    ).first()

    if hot_query:
        hot_query.frequency += 1
        if retrieval_score:
            hot_query.avg_retrieval_score = (hot_query.avg_retrieval_score + retrieval_score) / 2
        hot_query.miss_rate = (hot_query.miss_rate + (1 if is_miss else 0)) / 2
        hot_query.last_seen_at = datetime.utcnow()
    else:
        hot_query = HotQuery(
            enterprise_id=enterprise_id,
            query_text=query,
            query_normalized=normalized_query,
            frequency=1,
            avg_retrieval_score=retrieval_score,
            miss_rate=1 if is_miss else 0
        )
        db.add(hot_query)

    # 如果未命中且分数很低，记录到未命中表
    if is_miss and retrieval_score and retrieval_score < 0.3:
        missed = MissedQuery(
            enterprise_id=enterprise_id,
            query=query,
            session_id=session_id,
            user_id=user_id,
            retrieval_score=retrieval_score,
            status="pending"
        )
        db.add(missed)

    db.commit()

    return {"id": str(query_log.id), "is_miss": is_miss}


@app.get("/api/v1/query-logs")
async def list_query_logs(
    enterprise_id: UUID,
    response_type: Optional[str] = None,
    is_miss: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取查询日志"""
    query = db.query(QueryLog).filter(QueryLog.enterprise_id == enterprise_id)

    if response_type:
        query = query.filter(QueryLog.response_type == response_type)
    if is_miss is not None:
        query = query.filter(QueryLog.is_miss == is_miss)
    if start_date:
        query = query.filter(QueryLog.created_at >= start_date)
    if end_date:
        query = query.filter(QueryLog.created_at <= end_date)

    logs = query.order_by(QueryLog.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": str(log.id),
            "query": log.query,
            "response_type": log.response_type,
            "retrieval_score": log.retrieval_score,
            "is_miss": log.is_miss,
            "tokens_used": log.tokens_used,
            "response_time_ms": log.response_time_ms,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]


# ============ 热词统计 ============

@app.get("/api/v1/hot-queries")
async def get_hot_queries(
    enterprise_id: UUID,
    limit: int = Query(default=10, le=100),
    time_range: Optional[str] = "all",
    db: Session = Depends(get_db)
):
    """
    获取 Top N 热门查询
    - time_range: "day" | "week" | "month" | "all"
    """
    query = db.query(HotQuery).filter(HotQuery.enterprise_id == enterprise_id)

    if time_range == "day":
        query = query.filter(HotQuery.last_seen_at >= datetime.utcnow() - timedelta(days=1))
    elif time_range == "week":
        query = query.filter(HotQuery.last_seen_at >= datetime.utcnow() - timedelta(weeks=1))
    elif time_range == "month":
        query = query.filter(HotQuery.last_seen_at >= datetime.utcnow() - timedelta(days=30))

    hot_queries = query.order_by(desc('frequency')).limit(limit).all()

    return [
        {
            "query": hq.query_text,
            "frequency": hq.frequency,
            "avg_score": round(hq.avg_retrieval_score, 3) if hq.avg_retrieval_score else None,
            "miss_rate": round(hq.miss_rate * 100, 2) if hq.miss_rate else 0,
            "last_seen": hq.last_seen_at.isoformat()
        }
        for hq in hot_queries
    ]


@app.get("/api/v1/unanswered-queries")
async def get_unanswered_queries(
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取高频但未命中的问题（需要补充到知识库）
    """
    queries = db.query(HotQuery).filter(
        HotQuery.enterprise_id == enterprise_id,
        HotQuery.miss_rate > 0.5
    ).order_by(desc('frequency')).offset(skip).limit(limit).all()

    return [
        {
            "query": q.query_text,
            "frequency": q.frequency,
            "miss_rate": round(q.miss_rate * 100, 2),
            "suggestion": "建议添加到知识库或FAQ"
        }
        for q in queries
    ]


# ============ 未命中日志 ============

@app.get("/api/v1/missed-queries")
async def list_missed_queries(
    enterprise_id: UUID,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取未命中问题列表"""
    query = db.query(MissedQuery).filter(MissedQuery.enterprise_id == enterprise_id)

    if status:
        query = query.filter(MissedQuery.status == status)

    missed = query.order_by(MissedQuery.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": str(m.id),
            "query": m.query,
            "retrieval_score": m.retrieval_score,
            "status": m.status,
            "suggested_answer": m.suggested_answer,
            "created_at": m.created_at.isoformat()
        }
        for m in missed
    ]


@app.put("/api/v1/missed-queries/{query_id}/resolve")
async def resolve_missed_query(
    query_id: UUID,
    suggested_answer: str,
    resolution_notes: Optional[str] = None,
    resolved_by: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """标记未命中问题已解决"""
    missed = db.query(MissedQuery).filter(MissedQuery.id == query_id).first()

    if not missed:
        raise HTTPException(status_code=404, detail="Missed query not found")

    missed.status = "resolved"
    missed.suggested_answer = suggested_answer
    missed.resolution_notes = resolution_notes
    missed.resolved_by = resolved_by
    missed.resolved_at = datetime.utcnow()

    db.commit()

    return {"message": "Missed query resolved", "id": str(query_id)}


# ============ 会话存档 ============

@app.post("/api/v1/archives")
async def create_archive(
    session_id: UUID,
    user_id: UUID,
    enterprise_id: UUID,
    title: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    summary: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建会话存档"""
    archive = ConversationArchive(
        session_id=session_id,
        user_id=user_id,
        enterprise_id=enterprise_id,
        title=title or f"会话存档 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        duration_seconds=duration_seconds,
        summary=summary,
        status="archived",
        archived_at=datetime.utcnow()
    )
    db.add(archive)
    db.commit()
    db.refresh(archive)

    return {
        "id": str(archive.id),
        "title": archive.title,
        "created_at": archive.created_at.isoformat()
    }


@app.get("/api/v1/archives")
async def list_archives(
    enterprise_id: UUID,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取会话存档列表"""
    query = db.query(ConversationArchive).filter(
        ConversationArchive.enterprise_id == enterprise_id,
        ConversationArchive.status == "archived"
    )

    if user_id:
        query = query.filter(ConversationArchive.user_id == user_id)
    if start_date:
        query = query.filter(ConversationArchive.archived_at >= start_date)
    if end_date:
        query = query.filter(ConversationArchive.archived_at <= end_date)

    archives = query.order_by(ConversationArchive.archived_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": str(a.id),
            "session_id": str(a.session_id),
            "title": a.title,
            "message_count": a.message_count,
            "duration_seconds": a.duration_seconds,
            "summary": a.summary,
            "archived_at": a.archived_at.isoformat() if a.archived_at else None
        }
        for a in archives
    ]


@app.get("/api/v1/archives/{archive_id}")
async def get_archive(
    archive_id: UUID,
    db: Session = Depends(get_db)
):
    """获取存档详情"""
    archive = db.query(ConversationArchive).filter(
        ConversationArchive.id == archive_id
    ).first()

    if not archive:
        raise HTTPException(status_code=404, detail="Archive not found")

    return {
        "id": str(archive.id),
        "session_id": str(archive.session_id),
        "title": archive.title,
        "message_count": archive.message_count,
        "duration_seconds": archive.duration_seconds,
        "summary": archive.summary,
        "status": archive.status,
        "created_at": archive.created_at.isoformat(),
        "archived_at": archive.archived_at.isoformat() if archive.archived_at else None
    }


# ============ 仪表盘统计 ============

@app.get("/api/v1/dashboard")
async def get_dashboard_stats(
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """获取仪表盘统计数据"""
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)

    total_sessions = db.query(func.count(ConversationArchive.id)).filter(
        ConversationArchive.enterprise_id == enterprise_id
    ).scalar() or 0

    today_sessions = db.query(func.count(ConversationArchive.id)).filter(
        ConversationArchive.enterprise_id == enterprise_id,
        ConversationArchive.archived_at >= today
    ).scalar() or 0

    total_queries = db.query(func.count(QueryLog.id)).filter(
        QueryLog.enterprise_id == enterprise_id
    ).scalar() or 0

    week_queries = db.query(func.count(QueryLog.id)).filter(
        QueryLog.enterprise_id == enterprise_id,
        QueryLog.created_at >= week_ago
    ).scalar() or 0

    miss_count = db.query(func.count(QueryLog.id)).filter(
        QueryLog.enterprise_id == enterprise_id,
        QueryLog.is_miss == True
    ).scalar() or 0

    avg_score = db.query(func.avg(QueryLog.retrieval_score)).filter(
        QueryLog.enterprise_id == enterprise_id,
        QueryLog.retrieval_score.isnot(None)
    ).scalar()

    positive_rate = db.query(
        func.count(MessageFeedback.id)
    ).filter(
        MessageFeedback.enterprise_id == enterprise_id,
        MessageFeedback.rating == "thumbs_up"
    ).scalar() or 0

    total_feedback = db.query(func.count(MessageFeedback.id)).filter(
        MessageFeedback.enterprise_id == enterprise_id
    ).scalar() or 0

    pending_alerts = db.query(func.count(MissedQuery.id)).filter(
        MissedQuery.enterprise_id == enterprise_id,
        MissedQuery.status == "pending"
    ).scalar() or 0

    return {
        "sessions": {
            "total": total_sessions,
            "today": today_sessions
        },
        "queries": {
            "total": total_queries,
            "this_week": week_queries,
            "miss_count": miss_count,
            "miss_rate": round(miss_count / total_queries * 100, 2) if total_queries > 0 else 0,
            "avg_retrieval_score": round(avg_score, 3) if avg_score else None
        },
        "feedback": {
            "total": total_feedback,
            "positive_rate": round(positive_rate / total_feedback * 100, 2) if total_feedback > 0 else 0
        },
        "alerts": {
            "pending": pending_alerts
        }
    }


@app.on_event("startup")
async def startup():
    print("Analytics Service starting up...")
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
    await redis_manager.connect()


@app.on_event("shutdown")
async def shutdown():
    print("Analytics Service shutting down...")
    await redis_manager.disconnect()
