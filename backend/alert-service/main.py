"""
Alert Service - Alert and Human Intervention Management

Enhanced features:
- Emotion recognition for detecting user sentiment
- Human takeover logic for escalating difficult conversations
- Ticket system integration
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from .config import settings
from .database import get_db, init_db
from .models import Alert
from .emotion_recognizer import EmotionRecognizer
from .human_takeover import get_human_takeover_service


app = FastAPI(
    title="Alert Service",
    description="Alert and Human Intervention Service with emotion recognition",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Singleton instances
emotion_recognizer = EmotionRecognizer()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "alert-service", "version": "2.0.0"}


@app.get("/api/v1/alerts")
async def list_alerts(
    enterprise_id: UUID,
    status: str = None,
    priority: str = None,
    alert_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List alerts for an enterprise"""
    query = db.query(Alert).filter(Alert.enterprise_id == enterprise_id)
    
    if status:
        query = query.filter(Alert.status == status)
    if priority:
        query = query.filter(Alert.priority == priority)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(a.id),
            "user_id": str(a.user_id),
            "session_id": str(a.session_id),
            "message_id": str(a.message_id) if a.message_id else None,
            "alert_type": a.alert_type,
            "trigger_word": a.trigger_word,
            "content": a.content,
            "priority": a.priority,
            "status": a.status,
            "assigned_to": str(a.assigned_to) if a.assigned_to else None,
            "created_at": a.created_at.isoformat()
        }
        for a in alerts
    ]


@app.get("/api/v1/alerts/{alert_id}")
async def get_alert(alert_id: UUID, db: Session = Depends(get_db)):
    """Get alert details"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "id": str(alert.id),
        "user_id": str(alert.user_id),
        "session_id": str(alert.session_id),
        "message_id": str(alert.message_id) if alert.message_id else None,
        "alert_type": alert.alert_type,
        "trigger_word": alert.trigger_word,
        "content": alert.content,
        "priority": alert.priority,
        "status": alert.status,
        "assigned_to": str(alert.assigned_to) if alert.assigned_to else None,
        "resolution_notes": alert.resolution_notes,
        "created_at": alert.created_at.isoformat(),
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
    }


@app.put("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    assigned_to: UUID = None,
    db: Session = Depends(get_db)
):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.utcnow()
    if assigned_to:
        alert.assigned_to = assigned_to
    
    db.commit()
    
    return {"message": "Alert acknowledged", "alert_id": str(alert_id)}


@app.put("/api/v1/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    resolution_notes: str = None,
    db: Session = Depends(get_db)
):
    """Resolve an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    if resolution_notes:
        alert.resolution_notes = resolution_notes
    
    db.commit()
    
    return {"message": "Alert resolved", "alert_id": str(alert_id)}


@app.get("/api/v1/alerts/stats")
async def get_alert_stats(
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """Get alert statistics"""
    alerts = db.query(Alert).filter(Alert.enterprise_id == enterprise_id).all()
    
    stats = {
        "total": len(alerts),
        "pending": len([a for a in alerts if a.status == "pending"]),
        "acknowledged": len([a for a in alerts if a.status == "acknowledged"]),
        "resolved": len([a for a in alerts if a.status == "resolved"]),
        "by_priority": {
            "urgent": len([a for a in alerts if a.priority == "urgent"]),
            "high": len([a for a in alerts if a.priority == "high"]),
            "medium": len([a for a in alerts if a.priority == "medium"]),
            "low": len([a for a in alerts if a.priority == "low"])
        },
        "by_type": {}
    }
    
    for alert in alerts:
        alert_type = alert.alert_type
        if alert_type not in stats["by_type"]:
            stats["by_type"][alert_type] = 0
        stats["by_type"][alert_type] += 1
    
    return stats


@app.get("/api/v1/alerts/pending")
async def get_pending_alerts(
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """Get pending alerts that need attention"""
    alerts = db.query(Alert).filter(
        Alert.enterprise_id == enterprise_id,
        Alert.status.in_(["pending", "acknowledged"])
    ).order_by(
        Alert.priority.desc(),
        Alert.created_at.asc()
    ).all()
    
    return [
        {
            "id": str(a.id),
            "alert_type": a.alert_type,
            "priority": a.priority,
            "content": a.content,
            "created_at": a.created_at.isoformat(),
            "assigned_to": str(a.assigned_to) if a.assigned_to else None
        }
        for a in alerts
    ]


# ==================== 管理员API端点 ====================

@app.get("/api/v1/admin/alerts")
async def admin_list_alerts(
    enterprise_id: UUID,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    alert_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    管理员获取告警列表

    供admin-service调用，返回指定企业的所有告警

    参数:
        enterprise_id: 企业ID
        status: 状态筛选（可选）
        priority: 优先级筛选（可选）
        alert_type: 告警类型筛选（可选）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        告警列表
    """
    query = db.query(Alert).filter(Alert.enterprise_id == enterprise_id)

    if status:
        query = query.filter(Alert.status == status)
    if priority:
        query = query.filter(Alert.priority == priority)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)

    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": str(a.id),
            "user_id": str(a.user_id),
            "session_id": str(a.session_id),
            "message_id": str(a.message_id) if a.message_id else None,
            "alert_type": a.alert_type,
            "trigger_word": a.trigger_word,
            "content": a.content,
            "priority": a.priority,
            "status": a.status,
            "assigned_to": str(a.assigned_to) if a.assigned_to else None,
            "resolution_notes": a.resolution_notes,
            "created_at": a.created_at.isoformat(),
            "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None
        }
        for a in alerts
    ]


@app.get("/api/v1/admin/alerts/{alert_id}")
async def admin_get_alert(
    alert_id: UUID,
    db: Session = Depends(get_db)
):
    """
    管理员获取告警详情

    供admin-service调用，返回指定告警的详细信息

    参数:
        alert_id: 告警ID

    返回:
        告警详情
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "id": str(alert.id),
        "user_id": str(alert.user_id),
        "session_id": str(alert.session_id),
        "message_id": str(alert.message_id) if alert.message_id else None,
        "alert_type": alert.alert_type,
        "trigger_word": alert.trigger_word,
        "content": alert.content,
        "priority": alert.priority,
        "status": alert.status,
        "assigned_to": str(alert.assigned_to) if alert.assigned_to else None,
        "resolution_notes": alert.resolution_notes,
        "created_at": alert.created_at.isoformat(),
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
    }


@app.get("/api/v1/admin/alerts/stats")
async def admin_get_alert_stats(
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """
    管理员获取告警统计

    供admin-service调用，返回指定企业的告警统计数据

    参数:
        enterprise_id: 企业ID

    返回:
        告警统计数据
    """
    alerts = db.query(Alert).filter(Alert.enterprise_id == enterprise_id).all()

    stats = {
        "total": len(alerts),
        "pending": len([a for a in alerts if a.status == "pending"]),
        "acknowledged": len([a for a in alerts if a.status == "acknowledged"]),
        "resolved": len([a for a in alerts if a.status == "resolved"]),
        "by_priority": {
            "urgent": len([a for a in alerts if a.priority == "urgent"]),
            "high": len([a for a in alerts if a.priority == "high"]),
            "medium": len([a for a in alerts if a.priority == "medium"]),
            "low": len([a for a in alerts if a.priority == "low"])
        },
        "by_type": {}
    }

    for alert in alerts:
        alert_type = alert.alert_type
        if alert_type not in stats["by_type"]:
            stats["by_type"][alert_type] = 0
        stats["by_type"][alert_type] += 1

    return stats


@app.get("/api/v1/admin/alerts/pending")
async def admin_get_pending_alerts(
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    管理员获取待处理告警

    供admin-service调用，返回指定企业的待处理告警

    参数:
        enterprise_id: 企业ID
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        待处理告警列表
    """
    alerts = db.query(Alert).filter(
        Alert.enterprise_id == enterprise_id,
        Alert.status.in_(["pending", "acknowledged"])
    ).order_by(
        Alert.priority.desc(),
        Alert.created_at.asc()
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": str(a.id),
            "user_id": str(a.user_id),
            "session_id": str(a.session_id),
            "alert_type": a.alert_type,
            "content": a.content,
            "priority": a.priority,
            "status": a.status,
            "assigned_to": str(a.assigned_to) if a.assigned_to else None,
            "created_at": a.created_at.isoformat()
        }
        for a in alerts
    ]


@app.put("/api/v1/admin/alerts/{alert_id}/acknowledge")
async def admin_acknowledge_alert(
    alert_id: UUID,
    assigned_to: UUID = None,
    db: Session = Depends(get_db)
):
    """
    管理员确认告警

    供admin-service调用，确认指定告警

    参数:
        alert_id: 告警ID
        assigned_to: 分配给的用户ID（可选）

    返回:
        确认结果
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.utcnow()
    if assigned_to:
        alert.assigned_to = assigned_to

    db.commit()

    return {"message": "Alert acknowledged", "alert_id": str(alert_id)}


@app.put("/api/v1/admin/alerts/{alert_id}/resolve")
async def admin_resolve_alert(
    alert_id: UUID,
    resolution_notes: str = None,
    db: Session = Depends(get_db)
):
    """
    管理员解决告警

    供admin-service调用，解决指定告警

    参数:
        alert_id: 告警ID
        resolution_notes: 解决备注（可选）

    返回:
        解决结果
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    if resolution_notes:
        alert.resolution_notes = resolution_notes

    db.commit()

    return {"message": "Alert resolved", "alert_id": str(alert_id)}


# ==================== Emotion Recognition API ====================

@app.post("/api/v1/emotion/analyze")
async def analyze_emotion(text: str):
    """
    Analyze emotion from text
    
    Args:
        text: User input text to analyze
    
    Returns:
        Emotion analysis results including dominant emotion, scores, and intensity
    """
    result = emotion_recognizer.analyze_emotion(text)
    return result


# ==================== Human Takeover API ====================

@app.post("/api/v1/takeover/check")
async def check_takeover_needed(
    user_id: UUID,
    session_id: UUID,
    enterprise_id: UUID,
    message: str,
    conversation_history: List[Dict[str, str]] = None,
    retrieval_score: float = None,
    consecutive_failures: int = 0
):
    """
    Check if human takeover is needed based on various signals
    
    Args:
        user_id: User ID
        session_id: Session ID
        enterprise_id: Enterprise ID
        message: Current user message
        conversation_history: List of previous messages
        retrieval_score: RAG retrieval confidence score (0-1)
        consecutive_failures: Number of consecutive failed attempts
    
    Returns:
        Decision on whether takeover is needed and reasons
    """
    takeover_service = get_human_takeover_service()
    
    result = takeover_service.check_takeover_needed(
        user_id=user_id,
        session_id=session_id,
        message=message,
        conversation_history=conversation_history or [],
        enterprise_id=enterprise_id,
        retrieval_score=retrieval_score,
        consecutive_failures=consecutive_failures
    )
    
    return result


@app.post("/api/v1/takeover/create")
async def create_takeover(
    user_id: UUID,
    session_id: UUID,
    enterprise_id: UUID,
    message_id: UUID = None,
    content: str = None,
    reasons: List[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a human takeover alert/ticket
    
    Args:
        user_id: User ID
        session_id: Session ID
        enterprise_id: Enterprise ID
        message_id: Message ID that triggered takeover
        content: Content that triggered takeover
        reasons: List of reasons for takeover
    
    Returns:
        Created alert details
    """
    takeover_service = get_human_takeover_service()
    
    alert = takeover_service.create_takeover_alert(
        user_id=user_id,
        session_id=session_id,
        enterprise_id=enterprise_id,
        message_id=message_id,
        content=content,
        reasons=reasons,
        db=db
    )
    
    return {
        "message": "Takeover alert created",
        "alert_id": str(alert.id),
        "status": alert.status,
        "created_at": alert.created_at.isoformat()
    }


@app.put("/api/v1/takeover/{alert_id}/assign")
async def assign_takeover(
    alert_id: UUID,
    agent_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Assign takeover alert to a human agent
    
    Args:
        alert_id: Alert ID
        agent_id: Agent user ID to assign
    
    Returns:
        Updated alert details
    """
    takeover_service = get_human_takeover_service()
    
    alert = takeover_service.assign_to_agent(alert_id, agent_id, db)
    
    return {
        "message": "Alert assigned",
        "alert_id": str(alert.id),
        "assigned_to": str(alert.assigned_to),
        "status": alert.status
    }


@app.post("/api/v1/alerts")
async def create_alert(
    user_id: UUID,
    session_id: UUID,
    enterprise_id: UUID,
    alert_type: str,
    content: str = None,
    trigger_word: str = None,
    message_id: UUID = None,
    priority: str = "medium",
    db: Session = Depends(get_db)
):
    """
    Create a new alert
    
    Args:
        user_id: User ID
        session_id: Session ID
        enterprise_id: Enterprise ID
        alert_type: Type of alert (SENSITIVE_CONTENT, HUMAN_TAKEOVER, etc.)
        content: Content that triggered the alert
        trigger_word: Specific word that triggered the alert
        message_id: Message ID reference
        priority: Alert priority (low, medium, high, urgent)
    
    Returns:
        Created alert details
    """
    alert = Alert(
        user_id=user_id,
        session_id=session_id,
        enterprise_id=enterprise_id,
        alert_type=alert_type,
        content=content,
        trigger_word=trigger_word,
        message_id=message_id,
        priority=priority,
        status="pending"
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return {
        "message": "Alert created",
        "alert_id": str(alert.id),
        "status": alert.status,
        "created_at": alert.created_at.isoformat()
    }


@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    print("Alert Service starting up...")
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    print("Alert Service shutting down...")
