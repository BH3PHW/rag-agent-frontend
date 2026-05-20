"""
Chat database models
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, JSON
import uuid

try:
    from .database import Base
except ImportError:
    from database import Base


def uuid_column():
    """兼容SQLite和PostgreSQL的UUID列"""
    return Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


def uuid_fk_column():
    """兼容SQLite和PostgreSQL的UUID外键列"""
    return Column(String(36), nullable=False)


class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"
    
    id = uuid_column()
    user_id = uuid_fk_column()
    enterprise_id = uuid_fk_column()
    title = Column(String(200))
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id})>"


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = uuid_column()
    session_id = uuid_fk_column()
    user_id = Column(String(36), nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=[])
    is_sensitive = Column(Boolean, default=False)
    requires_human = Column(Boolean, default=False)
    tokens_used = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role})>"
