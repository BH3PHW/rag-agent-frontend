"""
FAQ Management Service
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from .database import Base


class FAQ(Base):
    """常见问题表"""
    __tablename__ = "faqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    keywords = Column(ARRAY(String), default=[])  # 关键词列表，用于精确匹配
    category = Column(String(50))  # 问题分类
    priority = Column(Integer, default=0)  # 优先级，越高越先匹配
    hit_count = Column(Integer, default=0)  # 命中次数
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FAQ(id={self.id}, question={self.question[:50]})>"


class KBVersion(Base):
    """知识库版本快照"""
    __tablename__ = "kb_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    snapshot_name = Column(String(200))
    description = Column(Text)
    document_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    snapshot_data = Column(Text)  # JSON格式的快照数据
    is_current = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KBVersion(id={self.id}, version={self.version_number})>"


class DocumentVersion(Base):
    """文档版本历史"""
    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(500))
    file_hash = Column(String(64))  # MD5哈希
    file_size = Column(Integer)
    change_notes = Column(Text)
    is_current = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DocumentVersion(id={self.id}, version={self.version_number})>"
