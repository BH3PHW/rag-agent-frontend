"""
Chat Service 数据模型扩展 - 问答质量评估相关表
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
import uuid

# 从同一模块导入 Base，与 ChatSession 和 ChatMessage 使用相同的基类
try:
    from .models import Base, uuid_column, uuid_fk_column
except ImportError:
    from models import Base, uuid_column, uuid_fk_column


class Feedback(Base):
    """用户反馈表 - 用于记录点赞/点踩
    
    字段要求：
    - id: 主键
    - message_id: 关联对话消息
    - user_id: 用户ID
    - rating: 点赞/点踩
    - reason: 点踩原因，可选
    - created_at: 创建时间
    """
    __tablename__ = "feedback"

    id = uuid_column()
    message_id = uuid_fk_column()
    user_id = Column(String(36), nullable=False)
    rating = Column(String(20), nullable=False)  # "thumbs_up" | "thumbs_down"
    reason = Column(Text)  # 点踩原因，可选
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Feedback(id={self.id}, rating={self.rating})>"


class UnmatchedQuestion(Base):
    """未匹配问题表 - 用于存储检索相似度低于阈值的用户提问
    
    字段要求：
    - id: 主键
    - session_id: 会话ID
    - user_id: 用户ID
    - question: 用户提问
    - retrieval_score: 检索相似度分数
    - created_at: 创建时间
    """
    __tablename__ = "unmatched_questions"

    id = uuid_column()
    session_id = uuid_fk_column()
    user_id = Column(String(36), nullable=False)
    question = Column(Text, nullable=False)
    retrieval_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UnmatchedQuestion(id={self.id}, score={self.retrieval_score})>"
