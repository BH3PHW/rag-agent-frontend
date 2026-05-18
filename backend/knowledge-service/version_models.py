"""
Knowledge Base Version Control Models
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from .database import Base


class DocumentVersion(Base):
    """Document version tracking model"""
    __tablename__ = "document_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)
    status = Column(String(20), default="draft")  # draft, published, archived
    is_active = Column(Boolean, default=False)
    changes = Column(JSONB, default={})  # What changed in this version
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    
    def __repr__(self):
        return f"<DocumentVersion(id={self.id}, version={self.version_number})>"


class KnowledgeBaseVersion(Base):
    """Knowledge base version for gray release"""
    __tablename__ = "knowledge_base_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False)
    version_tag = Column(String(50), nullable=False)  # e.g., "v1.0.0"
    description = Column(Text)
    status = Column(String(20), default="draft")  # draft, staging, published, archived
    traffic_percentage = Column(Integer, default=0)  # For canary release (0-100)
    document_versions = Column(JSONB, default={})  # Mapping of doc_id -> version_id
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    rolled_back_at = Column(DateTime)
    
    def __repr__(self):
        return f"<KnowledgeBaseVersion(id={self.id}, tag={self.version_tag})>"


class IncrementalUpdateTask(Base):
    """Track incremental update tasks"""
    __tablename__ = "incremental_update_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    task_type = Column(String(20), nullable=False)  # create, update, delete, reindex
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<IncrementalUpdateTask(id={self.id}, type={self.task_type}, status={self.status})>"
