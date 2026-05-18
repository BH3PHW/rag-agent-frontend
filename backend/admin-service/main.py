"""
Admin Service - Operational Dashboard Backend
"""
from fastapi import FastAPI, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import asyncio
import json

from .config import settings
from .database import get_db, init_db


app = FastAPI(
    title="Admin Service",
    description="Admin Dashboard Backend for RAG Customer Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "admin-service"}


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "subscribe":
                enterprise_id = message.get("enterprise_id")
                await websocket.send_json({
                    "type": "subscribed",
                    "enterprise_id": enterprise_id
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/v1/admin/overview")
async def get_overview(enterprise_id: UUID, db: Session = Depends(get_db)):
    """获取企业运营概览"""
    from analytics_service.models import QueryLog, MessageFeedback, HotQuery, MissedQuery
    from chat_service.models import ChatSession

    total_sessions = db.query(ChatSession).filter(
        ChatSession.enterprise_id == enterprise_id
    ).count()

    total_queries = db.query(QueryLog).filter(
        QueryLog.enterprise_id == enterprise_id
    ).count()

    pending_alerts = db.query(MissedQuery).filter(
        MissedQuery.enterprise_id == enterprise_id,
        MissedQuery.status == "pending"
    ).count()

    positive_feedback = db.query(MessageFeedback).filter(
        MessageFeedback.enterprise_id == enterprise_id,
        MessageFeedback.rating == "thumbs_up"
    ).count()

    total_feedback = db.query(MessageFeedback).filter(
        MessageFeedback.enterprise_id == enterprise_id
    ).count()

    return {
        "total_sessions": total_sessions,
        "total_queries": total_queries,
        "pending_alerts": pending_alerts,
        "positive_rate": round(positive_feedback / total_feedback * 100, 2) if total_feedback > 0 else 0
    }


@app.get("/api/v1/admin/realtime")
async def get_realtime_stats(enterprise_id: UUID, db: Session = Depends(get_db)):
    """获取实时统计"""
    from analytics_service.models import QueryLog
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    queries_last_hour = db.query(QueryLog).filter(
        QueryLog.enterprise_id == enterprise_id,
        QueryLog.created_at >= hour_ago
    ).count()

    queries_today = db.query(QueryLog).filter(
        QueryLog.enterprise_id == enterprise_id,
        QueryLog.created_at >= day_ago
    ).count()

    return {
        "queries_last_hour": queries_last_hour,
        "queries_today": queries_today,
        "timestamp": now.isoformat()
    }


@app.get("/api/v1/admin/performance")
async def get_performance_metrics(
    enterprise_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """获取性能指标"""
    from analytics_service.models import QueryLog
    from sqlalchemy import func

    query = db.query(QueryLog).filter(QueryLog.enterprise_id == enterprise_id)

    if start_date:
        query = query.filter(QueryLog.created_at >= start_date)
    if end_date:
        query = query.filter(QueryLog.created_at <= end_date)

    total = query.count()
    avg_score = query.with_entities(func.avg(QueryLog.retrieval_score)).scalar()
    avg_response_time = query.with_entities(func.avg(QueryLog.response_time_ms)).scalar()
    total_tokens = query.with_entities(func.sum(QueryLog.tokens_used)).scalar()

    response_types = db.query(
        QueryLog.response_type,
        func.count(QueryLog.id)
    ).filter(
        QueryLog.enterprise_id == enterprise_id
    ).group_by(QueryLog.response_type).all()

    return {
        "total_queries": total,
        "avg_retrieval_score": round(avg_score, 3) if avg_score else None,
        "avg_response_time_ms": round(avg_response_time) if avg_response_time else None,
        "total_tokens": total_tokens or 0,
        "response_type_distribution": {rt: count for rt, count in response_types}
    }


@app.get("/api/v1/admin/alerts")
async def get_pending_alerts(
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取待处理告警"""
    from alert_service.models import Alert

    alerts = db.query(Alert).filter(
        Alert.enterprise_id == enterprise_id,
        Alert.status.in_(["pending", "acknowledged"])
    ).order_by(
        Alert.priority.desc(),
        Alert.created_at.desc()
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": str(a.id),
            "alert_type": a.alert_type,
            "priority": a.priority,
            "content": a.content,
            "status": a.status,
            "created_at": a.created_at.isoformat()
        }
        for a in alerts
    ]


@app.get("/api/v1/admin/knowledge-base/stats")
async def get_kb_stats(
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """获取知识库统计"""
    from knowledge_service.models import KnowledgeBase, Document

    kbs = db.query(KnowledgeBase).filter(
        KnowledgeBase.enterprise_id == enterprise_id
    ).all()

    total_docs = sum(kb.document_count for kb in kbs)
    total_chunks = sum(kb.chunk_count for kb in kbs)

    return {
        "knowledge_base_count": len(kbs),
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "knowledge_bases": [
            {
                "id": str(kb.id),
                "name": kb.name,
                "document_count": kb.document_count,
                "chunk_count": kb.chunk_count
            }
            for kb in kbs
        ]
    }


@app.post("/api/v1/admin/sessions/{session_id}/transfer")
async def transfer_to_human(
    session_id: UUID,
    target_agent_id: UUID,
    db: Session = Depends(get_db)
):
    """将会话转接给人工客服"""
    from chat_service.models import ChatSession

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "message": "Session transferred to human agent",
        "session_id": str(session_id),
        "agent_id": str(target_agent_id)
    }


@app.on_event("startup")
async def startup():
    print("Admin Service starting up...")
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown():
    print("Admin Service shutting down...")
