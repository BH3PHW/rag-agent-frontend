"""
CRUD operations for Chat Service

包含会话、消息、FAQ、反馈等所有数据库操作的独立模块，
降低与业务逻辑的耦合度，便于测试和维护。
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .models import ChatSession, ChatMessage
from .quality_models import Feedback, UnmatchedQuestion
from .faq_models import FAQ


# ============ ChatSession CRUD ============

def get_session_by_id(db: Session, session_id: UUID) -> Optional[ChatSession]:
    """获取会话详情"""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def get_sessions(
    db: Session,
    user_id: Optional[UUID] = None,
    enterprise_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50
) -> List[ChatSession]:
    """获取会话列表"""
    query = db.query(ChatSession)
    
    if user_id:
        query = query.filter(ChatSession.user_id == user_id)
    if enterprise_id:
        query = query.filter(ChatSession.enterprise_id == enterprise_id)
    
    return query.order_by(desc(ChatSession.updated_at)).offset(skip).limit(limit).all()


def count_sessions(
    db: Session,
    user_id: Optional[UUID] = None,
    enterprise_id: Optional[UUID] = None
) -> int:
    """统计会话数量"""
    query = db.query(func.count(ChatSession.id))
    
    if user_id:
        query = query.filter(ChatSession.user_id == user_id)
    if enterprise_id:
        query = query.filter(ChatSession.enterprise_id == enterprise_id)
    
    return query.scalar() or 0


def create_session(
    db: Session,
    user_id: UUID,
    enterprise_id: UUID,
    title: Optional[str] = None
) -> ChatSession:
    """创建新会话"""
    if not title:
        title = f"会话 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    
    session = ChatSession(
        user_id=user_id,
        enterprise_id=enterprise_id,
        title=title
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session(
    db: Session,
    session_id: UUID,
    title: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Optional[ChatSession]:
    """更新会话"""
    session = get_session_by_id(db, session_id)
    if not session:
        return None
    
    if title is not None:
        session.title = title
    if is_active is not None:
        session.is_active = is_active
    
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session_id: UUID) -> bool:
    """删除会话"""
    session = get_session_by_id(db, session_id)
    if not session:
        return False
    
    # 级联删除相关消息
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return True


# ============ ChatMessage CRUD ============

def get_messages(
    db: Session,
    session_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[ChatMessage]:
    """获取会话消息列表"""
    return db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).offset(skip).limit(limit).all()


def get_recent_messages(
    db: Session,
    session_id: UUID,
    limit: int = 10
) -> List[str]:
    """获取会话最近消息内容列表（用于上下文）"""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
    
    return [msg.content for msg in reversed(messages)]


def create_message(
    db: Session,
    session_id: UUID,
    user_id: Optional[UUID],
    role: str,
    content: str,
    sources: Optional[List[dict]] = None,
    is_sensitive: bool = False,
    requires_human: bool = False
) -> ChatMessage:
    """创建新消息"""
    message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role=role,
        content=content,
        sources=sources or [],
        is_sensitive=is_sensitive,
        requires_human=requires_human
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # 更新会话的消息计数和更新时间
    session = get_session_by_id(db, session_id)
    if session:
        session.message_count += 1
        session.updated_at = datetime.utcnow()
        
        # 如果会话没有标题，使用第一句话作为标题
        if not session.title or session.title.startswith("会话 "):
            session.title = content[:50] + ("..." if len(content) > 50 else "")
        
        db.commit()
    
    return message


def delete_session_messages(db: Session, session_id: UUID) -> int:
    """删除会话的所有消息"""
    count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.commit()
    return count


# ============ Feedback CRUD ============

def create_feedback(
    db: Session,
    message_id: UUID,
    user_id: UUID,
    rating: str,
    reason: Optional[str] = None
) -> Feedback:
    """创建用户反馈"""
    feedback = Feedback(
        message_id=message_id,
        user_id=user_id,
        rating=rating,
        reason=reason
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback_by_message(db: Session, message_id: UUID) -> Optional[Feedback]:
    """获取消息的反馈"""
    return db.query(Feedback).filter(Feedback.message_id == message_id).first()


def get_feedbacks(
    db: Session,
    user_id: Optional[UUID] = None,
    rating: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Feedback]:
    """获取反馈列表"""
    query = db.query(Feedback)
    
    if user_id:
        query = query.filter(Feedback.user_id == user_id)
    if rating:
        query = query.filter(Feedback.rating == rating)
    
    return query.order_by(desc(Feedback.created_at)).offset(skip).limit(limit).all()


# ============ UnmatchedQuestion CRUD ============

def create_unmatched_question(
    db: Session,
    session_id: UUID,
    user_id: UUID,
    question: str,
    retrieval_score: float
) -> UnmatchedQuestion:
    """记录未匹配问题"""
    unmatched = UnmatchedQuestion(
        session_id=session_id,
        user_id=user_id,
        question=question,
        retrieval_score=retrieval_score
    )
    
    db.add(unmatched)
    db.commit()
    db.refresh(unmatched)
    return unmatched


def get_unmatched_questions(
    db: Session,
    enterprise_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> List[UnmatchedQuestion]:
    """获取未匹配问题列表"""
    query = db.query(UnmatchedQuestion)
    
    if enterprise_id:
        query = query.join(
            ChatSession,
            UnmatchedQuestion.session_id == ChatSession.id
        ).filter(ChatSession.enterprise_id == enterprise_id)
    
    return query.order_by(desc(UnmatchedQuestion.created_at)).offset(skip).limit(limit).all()


# ============ FAQ CRUD ============

def get_faq_by_id(db: Session, faq_id: UUID) -> Optional[FAQ]:
    """获取FAQ详情"""
    return db.query(FAQ).filter(FAQ.id == faq_id).first()


def get_faqs(
    db: Session,
    enterprise_id: UUID,
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[FAQ]:
    """获取FAQ列表"""
    query = db.query(FAQ).filter(FAQ.enterprise_id == enterprise_id)
    
    if is_active is not None:
        query = query.filter(FAQ.is_active == is_active)
    if category:
        query = query.filter(FAQ.category == category)
    
    return query.order_by(desc(FAQ.hit_count)).offset(skip).limit(limit).all()


def create_faq(
    db: Session,
    enterprise_id: UUID,
    question: str,
    answer: str,
    keywords: Optional[str] = None,
    category: Optional[str] = None
) -> FAQ:
    """创建FAQ"""
    faq = FAQ(
        enterprise_id=enterprise_id,
        question=question,
        answer=answer,
        keywords=keywords,
        category=category
    )
    
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


def update_faq(
    db: Session,
    faq_id: UUID,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    keywords: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Optional[FAQ]:
    """更新FAQ"""
    faq = get_faq_by_id(db, faq_id)
    if not faq:
        return None
    
    if question is not None:
        faq.question = question
    if answer is not None:
        faq.answer = answer
    if keywords is not None:
        faq.keywords = keywords
    if category is not None:
        faq.category = category
    if is_active is not None:
        faq.is_active = is_active
    
    faq.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(faq)
    return faq


def increment_faq_hit(db: Session, faq_id: UUID) -> Optional[FAQ]:
    """增加FAQ命中次数"""
    faq = get_faq_by_id(db, faq_id)
    if not faq:
        return None
    
    faq.hit_count += 1
    faq.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(faq)
    return faq


def delete_faq(db: Session, faq_id: UUID) -> bool:
    """删除FAQ"""
    faq = get_faq_by_id(db, faq_id)
    if not faq:
        return False
    
    db.delete(faq)
    db.commit()
    return True


# ============ Admin Statistics ============

def get_sessions_stats(
    db: Session,
    enterprise_id: Optional[UUID] = None
) -> dict:
    """获取会话统计数据"""
    query = db.query(
        func.count(ChatSession.id).label("total_sessions"),
        func.sum(ChatSession.message_count).label("total_messages"),
        func.count(func.distinct(ChatSession.user_id)).label("unique_users")
    )
    
    if enterprise_id:
        query = query.filter(ChatSession.enterprise_id == enterprise_id)
    
    result = query.first()
    return {
        "total_sessions": result[0] or 0,
        "total_messages": result[1] or 0,
        "unique_users": result[2] or 0
    }
