"""
Analytics Service Models
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Float, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

from .database import Base


class MessageFeedback(Base):
    """用户对消息的反馈（点赞/点踩）"""
    __tablename__ = "message_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False)
    rating = Column(String(20), nullable=False)  # "thumbs_up" | "thumbs_down"
    reason = Column(Text)  # 点踩时必须填写的原因
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('message_id', 'user_id', name='unique_message_feedback'),
        Index('idx_feedback_session', 'session_id'),
        Index('idx_feedback_enterprise', 'enterprise_id'),
    )

    def __repr__(self):
        return f"<MessageFeedback(id={self.id}, rating={self.rating})>"


class QueryLog(Base):
    """查询日志与埋点"""
    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False)
    query = Column(Text, nullable=False)
    response_type = Column(String(50))  # "faq" | "rag" | "rule" | "human"
    retrieval_score = Column(Float)  # 最高检索相似度
    is_miss = Column(Boolean, default=False)  # 是否未命中
    tokens_used = Column(Integer, default=0)
    response_time_ms = Column(Integer)
    sources_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    Index('idx_query_enterprise', 'enterprise_id'),
    Index('idx_query_miss', 'is_miss'),
    Index('idx_query_created', 'created_at'),

    def __repr__(self):
        return f"<QueryLog(id={self.id}, response_type={self.response_type})>"


class ConversationArchive(Base):
    """会话存档"""
    __tablename__ = "conversation_archives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False)
    title = Column(String(200))
    message_count = Column(Integer, default=0)
    duration_seconds = Column(Integer)  # 会话持续时间
    summary = Column(Text)  # AI生成的会话摘要
    status = Column(String(20), default="active")  # "active" | "archived" | "deleted"
    archived_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    Index('idx_archive_enterprise', 'enterprise_id'),
    Index('idx_archive_user', 'user_id'),
    Index('idx_archive_status', 'status'),

    def __repr__(self):
        return f"<ConversationArchive(id={self.id}, status={self.status})>"


class HotQuery(Base):
    """热词统计"""
    __tablename__ = "hot_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    query_normalized = Column(String(500))  # 标准化后的查询
    frequency = Column(Integer, default=1)
    avg_retrieval_score = Column(Float)
    miss_rate = Column(Float, default=0)  # 未命中率
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    UniqueConstraint('enterprise_id', 'query_normalized', name='unique_hot_query')
    Index('idx_hot_enterprise_freq', 'enterprise_id', frequency.desc()),

    def __repr__(self):
        return f"<HotQuery(query={self.query_text[:50]}, freq={self.frequency})>"


class MissedQuery(Base):
    """未命中问题日志"""
    __tablename__ = "missed_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False)
    query = Column(Text, nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    retrieval_score = Column(Float)
    status = Column(String(20), default="pending")  # "pending" | "resolved" | "ignored"
    suggested_answer = Column(Text)
    resolution_notes = Column(Text)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    Index('idx_miss_enterprise', 'enterprise_id'),
    Index('idx_miss_status', 'status'),

    def __repr__(self):
        return f"<MissedQuery(id={self.id}, score={self.retrieval_score})>"
