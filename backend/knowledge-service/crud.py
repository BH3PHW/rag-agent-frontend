"""
CRUD operations for Knowledge Service

知识库和文档的数据库操作独立模块，
降低与业务逻辑的耦合度，便于测试和维护。
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .models import KnowledgeBase, Document


# ============ KnowledgeBase CRUD ============

def get_knowledge_base_by_id(db: Session, kb_id: UUID) -> Optional[KnowledgeBase]:
    """获取知识库详情"""
    return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()


def get_knowledge_bases(
    db: Session,
    enterprise_id: UUID,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[KnowledgeBase]:
    """获取知识库列表"""
    query = db.query(KnowledgeBase).filter(
        KnowledgeBase.enterprise_id == enterprise_id
    )
    
    if is_active is not None:
        query = query.filter(KnowledgeBase.is_active == is_active)
    
    return query.order_by(desc(KnowledgeBase.updated_at)).offset(skip).limit(limit).all()


def create_knowledge_base(
    db: Session,
    enterprise_id: UUID,
    name: str,
    description: Optional[str] = None
) -> KnowledgeBase:
    """创建知识库"""
    kb = KnowledgeBase(
        enterprise_id=enterprise_id,
        name=name,
        description=description
    )
    
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb


def update_knowledge_base(
    db: Session,
    kb_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Optional[KnowledgeBase]:
    """更新知识库"""
    kb = get_knowledge_base_by_id(db, kb_id)
    if not kb:
        return None
    
    if name is not None:
        kb.name = name
    if description is not None:
        kb.description = description
    if is_active is not None:
        kb.is_active = is_active
    
    kb.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(kb)
    return kb


def delete_knowledge_base(db: Session, kb_id: UUID) -> bool:
    """删除知识库"""
    kb = get_knowledge_base_by_id(db, kb_id)
    if not kb:
        return False
    
    # 级联删除相关文档
    db.query(Document).filter(Document.knowledge_base_id == kb_id).delete()
    db.delete(kb)
    db.commit()
    return True


def count_knowledge_bases(db: Session, enterprise_id: UUID) -> int:
    """统计知识库数量"""
    return db.query(func.count(KnowledgeBase.id)).filter(
        KnowledgeBase.enterprise_id == enterprise_id
    ).scalar() or 0


def get_knowledge_bases_stats(db: Session, enterprise_id: UUID) -> dict:
    """获取知识库统计数据"""
    result = db.query(
        func.count(KnowledgeBase.id).label("total_kbs"),
        func.sum(KnowledgeBase.document_count).label("total_documents"),
        func.sum(KnowledgeBase.chunk_count).label("total_chunks")
    ).filter(
        KnowledgeBase.enterprise_id == enterprise_id
    ).first()
    
    return {
        "total_kbs": result[0] or 0,
        "total_documents": result[1] or 0,
        "total_chunks": result[2] or 0
    }


# ============ Document CRUD ============

def get_document_by_id(db: Session, doc_id: UUID) -> Optional[Document]:
    """获取文档详情"""
    return db.query(Document).filter(Document.id == doc_id).first()


def get_documents(
    db: Session,
    knowledge_base_id: Optional[UUID] = None,
    enterprise_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Document]:
    """获取文档列表"""
    query = db.query(Document)
    
    if knowledge_base_id:
        query = query.filter(Document.knowledge_base_id == knowledge_base_id)
    elif enterprise_id:
        query = query.join(
            KnowledgeBase,
            Document.knowledge_base_id == KnowledgeBase.id
        ).filter(KnowledgeBase.enterprise_id == enterprise_id)
    
    if status:
        query = query.filter(Document.status == status)
    
    return query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()


def create_document(
    db: Session,
    knowledge_base_id: UUID,
    filename: str,
    file_path: Optional[str] = None,
    file_size: Optional[int] = None,
    file_type: Optional[str] = None,
    file_hash: Optional[str] = None,
    metadata: Optional[dict] = None
) -> Document:
    """创建文档"""
    doc = Document(
        knowledge_base_id=knowledge_base_id,
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        file_hash=file_hash,
        metadata_=metadata or {},
        status="pending"
    )
    
    db.add(doc)
    
    # 更新知识库的文档计数
    kb = get_knowledge_base_by_id(db, knowledge_base_id)
    if kb:
        kb.document_count += 1
        kb.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(doc)
    return doc


def update_document(
    db: Session,
    doc_id: UUID,
    filename: Optional[str] = None,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
    chunk_count: Optional[int] = None
) -> Optional[Document]:
    """更新文档"""
    doc = get_document_by_id(db, doc_id)
    if not doc:
        return None
    
    if filename is not None:
        doc.filename = filename
    if status is not None:
        doc.status = status
    if error_message is not None:
        doc.error_message = error_message
    if chunk_count is not None:
        doc.chunk_count = chunk_count
        
        # 同步更新知识库的块计数
        kb = get_knowledge_base_by_id(db, doc.knowledge_base_id)
        if kb:
            kb.chunk_count += chunk_count
    
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, doc_id: UUID) -> bool:
    """删除文档"""
    doc = get_document_by_id(db, doc_id)
    if not doc:
        return False
    
    # 更新知识库的文档和块计数
    kb = get_knowledge_base_by_id(db, doc.knowledge_base_id)
    if kb:
        kb.document_count = max(0, kb.document_count - 1)
        kb.chunk_count = max(0, kb.chunk_count - (doc.chunk_count or 0))
        kb.updated_at = datetime.utcnow()
    
    db.delete(doc)
    db.commit()
    return True


def count_documents(
    db: Session,
    knowledge_base_id: Optional[UUID] = None,
    enterprise_id: Optional[UUID] = None
) -> int:
    """统计文档数量"""
    query = db.query(func.count(Document.id))
    
    if knowledge_base_id:
        query = query.filter(Document.knowledge_base_id == knowledge_base_id)
    elif enterprise_id:
        query = query.join(
            KnowledgeBase,
            Document.knowledge_base_id == KnowledgeBase.id
        ).filter(KnowledgeBase.enterprise_id == enterprise_id)
    
    return query.scalar() or 0


# ============ Batch Operations ============

def get_documents_by_ids(db: Session, doc_ids: List[UUID]) -> List[Document]:
    """批量获取文档"""
    return db.query(Document).filter(Document.id.in_(doc_ids)).all()


def update_documents_status(
    db: Session,
    doc_ids: List[UUID],
    status: str
) -> int:
    """批量更新文档状态"""
    count = db.query(Document).filter(
        Document.id.in_(doc_ids)
    ).update({"status": status, "updated_at": datetime.utcnow()})
    db.commit()
    return count


def delete_documents_by_knowledge_base(db: Session, knowledge_base_id: UUID) -> int:
    """删除知识库的所有文档"""
    count = db.query(Document).filter(
        Document.knowledge_base_id == knowledge_base_id
    ).delete()
    db.commit()
    return count
