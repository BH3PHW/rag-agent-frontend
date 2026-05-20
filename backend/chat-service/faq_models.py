"""
Chat Service FAQ Models - faq_table in SQLite
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Index
import uuid

try:
    from .database import Base
    from .models import uuid_column, uuid_fk_column
except ImportError:
    from database import Base
    from models import uuid_column, uuid_fk_column


class FAQ(Base):
    """FAQ Table for standard question-answer pairs

    Fields:
    - id: Primary key
    - enterprise_id: Enterprise foreign key
    - question: User question
    - answer: Standard answer
    - keywords: Search keywords array
    - category: FAQ category
    - is_active: Active status
    - hit_count: Number of times this FAQ was hit
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    """
    __tablename__ = "faq_table"

    id = uuid_column()
    enterprise_id = uuid_fk_column()
    question = Column(Text, nullable=False, index=True)
    answer = Column(Text, nullable=False)
    keywords = Column(String, nullable=True)  # comma-separated keywords
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for faster search
    __table_args__ = (
        Index("idx_faq_enterprise", "enterprise_id"),
    )

    def __repr__(self):
        return f"<FAQ(id={self.id}, question={self.question[:50]}...)>"
