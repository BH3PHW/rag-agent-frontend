"""
Alert database models
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from .database import Base


class Alert(Base):
    """Alert model for sensitive content and human intervention"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"))
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    trigger_word = Column(String(100))
    content = Column(Text)
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="pending")
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, status={self.status})>"
