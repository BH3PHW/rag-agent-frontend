from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import uuid

try:
    from database import Base
except ImportError:
    from .database import Base


class AgentStatus(str, PyEnum):
    ONLINE = "online"
    BUSY = "busy"
    OFFLINE = "offline"


class AgentSessionStatus(str, PyEnum):
    WAITING = "waiting"
    ACTIVE = "active"
    CLOSED = "closed"


def uuid_column():
    """兼容SQLite和PostgreSQL的UUID列"""
    return Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


def uuid_fk_column():
    """兼容SQLite和PostgreSQL的UUID外键列"""
    return Column(String(36), nullable=False, index=True)


class Agent(Base):
    __tablename__ = "agents"

    id = uuid_column()
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(String(20), default=AgentStatus.OFFLINE.value, nullable=False)
    current_chats = Column(Integer, default=0)
    total_chats = Column(Integer, default=0)
    max_concurrent_chats = Column(Integer, default=5)
    enterprise_id = uuid_fk_column()
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sessions = relationship("AgentSession", back_populates="agent")


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = uuid_column()
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), default=AgentSessionStatus.WAITING.value, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    enterprise_id = uuid_fk_column()
    user_name = Column(String(100), nullable=True)
    topic = Column(String(255), nullable=True)
    priority = Column(Integer, default=0)

    agent = relationship("Agent", back_populates="sessions")
