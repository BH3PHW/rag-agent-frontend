"""
Alert Service - Alert and Human Intervention Management
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from .config import settings
from .database import get_db, init_db
from .models import Alert


app = FastAPI(
    title="Alert Service",
    description="Alert and Human Intervention Service",
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
    """Health check endpoint"""
    return {"status": "healthy", "service": "alert-service"}


@app.get("/api/v1/alerts")
async def list_alerts(
    enterprise_id: UUID,
    status: str = None,
    priority: str = None,
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
    
    # Count by type
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
