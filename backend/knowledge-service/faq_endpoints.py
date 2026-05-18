"""
FAQ Management Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import json

from .config import settings
from .database import get_db
from .faq_models import FAQ, KBVersion, DocumentVersion
from .faq_engine import get_faq_matcher


router = APIRouter(prefix="/api/v1", tags=["FAQ Management"])


@router.post("/faqs")
async def create_faq(
    enterprise_id: UUID,
    question: str,
    answer: str,
    knowledge_base_id: Optional[UUID] = None,
    keywords: List[str] = [],
    category: Optional[str] = None,
    priority: int = 0,
    db: Session = Depends(get_db)
):
    """创建FAQ"""
    faq = FAQ(
        enterprise_id=enterprise_id,
        knowledge_base_id=knowledge_base_id,
        question=question,
        answer=answer,
        keywords=keywords,
        category=category,
        priority=priority
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)

    return {
        "id": str(faq.id),
        "question": faq.question,
        "answer": faq.answer,
        "created_at": faq.created_at.isoformat()
    }


@router.get("/faqs")
async def list_faqs(
    enterprise_id: UUID,
    knowledge_base_id: Optional[UUID] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取FAQ列表"""
    query = db.query(FAQ).filter(FAQ.enterprise_id == enterprise_id)

    if knowledge_base_id:
        query = query.filter(FAQ.knowledge_base_id == knowledge_base_id)
    if category:
        query = query.filter(FAQ.category == category)
    if is_active is not None:
        query = query.filter(FAQ.is_active == is_active)

    faqs = query.order_by(FAQ.priority.desc(), FAQ.hit_count.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": str(f.id),
            "question": f.question,
            "answer": f.answer,
            "keywords": f.keywords or [],
            "category": f.category,
            "priority": f.priority,
            "hit_count": f.hit_count,
            "is_active": f.is_active,
            "created_at": f.created_at.isoformat()
        }
        for f in faqs
    ]


@router.get("/faqs/{faq_id}")
async def get_faq(faq_id: UUID, db: Session = Depends(get_db)):
    """获取FAQ详情"""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()

    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    return {
        "id": str(faq.id),
        "question": faq.question,
        "answer": faq.answer,
        "keywords": faq.keywords or [],
        "category": faq.category,
        "priority": faq.priority,
        "hit_count": faq.hit_count,
        "is_active": faq.is_active
    }


@router.put("/faqs/{faq_id}")
async def update_faq(
    faq_id: UUID,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    category: Optional[str] = None,
    priority: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """更新FAQ"""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()

    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    if question is not None:
        faq.question = question
    if answer is not None:
        faq.answer = answer
    if keywords is not None:
        faq.keywords = keywords
    if category is not None:
        faq.category = category
    if priority is not None:
        faq.priority = priority
    if is_active is not None:
        faq.is_active = is_active

    db.commit()
    db.refresh(faq)

    return {"message": "FAQ updated", "id": str(faq.id)}


@router.delete("/faqs/{faq_id}")
async def delete_faq(faq_id: UUID, db: Session = Depends(get_db)):
    """删除FAQ（软删除）"""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()

    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    faq.is_active = False
    db.commit()

    return {"message": "FAQ deleted"}


@router.get("/faqs/match")
@router.post("/faqs/match")
async def match_faq(
    enterprise_id: UUID,
    query: str,
    knowledge_base_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    匹配用户问题到FAQ
    返回最佳匹配的FAQ及其答案
    """
    faq_query = db.query(FAQ).filter(
        FAQ.enterprise_id == enterprise_id,
        FAQ.is_active == True
    )

    if knowledge_base_id:
        faq_query = faq_query.filter(FAQ.knowledge_base_id == knowledge_base_id)

    faqs = faq_query.all()

    faq_dicts = [
        {
            "id": str(f.id),
            "question": f.question,
            "answer": f.answer,
            "keywords": f.keywords or [],
            "priority": f.priority
        }
        for f in faqs
    ]

    matcher = get_faq_matcher()
    matched = matcher.match(query, faq_dicts)

    if matched:
        faq_record = db.query(FAQ).filter(FAQ.id == UUID(matched["id"])).first()
        if faq_record:
            faq_record.hit_count += 1
            db.commit()

        return {
            "matched": True,
            "faq": {
                "id": matched["id"],
                "question": matched["question"],
                "answer": matched["answer"],
                "match_score": matched["match_score"]
            }
        }

    return {"matched": False, "faq": None}


# ============ 知识库版本控制 ============

@router.post("/knowledge-bases/{kb_id}/snapshot")
async def create_snapshot(
    kb_id: UUID,
    enterprise_id: UUID,
    snapshot_name: Optional[str] = None,
    description: Optional[str] = None,
    created_by: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """
    创建知识库快照
    """
    from .models import KnowledgeBase, Document

    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.enterprise_id == enterprise_id
    ).first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    current_version = db.query(KBVersion).filter(
        KBVersion.knowledge_base_id == kb_id,
        KBVersion.is_current == True
    ).first()

    new_version_number = (current_version.version_number + 1) if current_version else 1

    snapshot = KBVersion(
        knowledge_base_id=kb_id,
        enterprise_id=enterprise_id,
        version_number=new_version_number,
        snapshot_name=snapshot_name or f"快照 v{new_version_number}",
        description=description,
        document_count=kb.document_count,
        chunk_count=kb.chunk_count,
        is_current=True,
        created_by=created_by
    )
    db.add(snapshot)

    if current_version:
        current_version.is_current = False

    db.commit()
    db.refresh(snapshot)

    return {
        "id": str(snapshot.id),
        "version_number": snapshot.version_number,
        "snapshot_name": snapshot.snapshot_name,
        "created_at": snapshot.created_at.isoformat()
    }


@router.get("/knowledge-bases/{kb_id}/snapshots")
async def list_snapshots(
    kb_id: UUID,
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取快照列表"""
    snapshots = db.query(KBVersion).filter(
        KBVersion.knowledge_base_id == kb_id,
        KBVersion.enterprise_id == enterprise_id
    ).order_by(KBVersion.version_number.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": str(s.id),
            "version_number": s.version_number,
            "snapshot_name": s.snapshot_name,
            "description": s.description,
            "document_count": s.document_count,
            "chunk_count": s.chunk_count,
            "is_current": s.is_current,
            "created_at": s.created_at.isoformat()
        }
        for s in snapshots
    ]


@router.post("/knowledge-bases/{kb_id}/rollback/{version_id}")
async def rollback_to_snapshot(
    kb_id: UUID,
    version_id: UUID,
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """
    回滚到指定快照
    注意：这是一个高风险操作，需要谨慎使用
    """
    snapshot = db.query(KBVersion).filter(
        KBVersion.id == version_id,
        KBVersion.knowledge_base_id == kb_id,
        KBVersion.enterprise_id == enterprise_id
    ).first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    current = db.query(KBVersion).filter(
        KBVersion.knowledge_base_id == kb_id,
        KBVersion.is_current == True
    ).first()

    snapshot.is_current = True

    if current:
        current.is_current = False

    db.commit()

    return {
        "message": "Successfully rolled back",
        "rolled_back_to_version": snapshot.version_number
    }


@router.get("/knowledge-bases/{kb_id}/diff/{version_id}")
async def compare_snapshot(
    kb_id: UUID,
    version_id: UUID,
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """对比当前版本与指定快照的差异"""
    snapshot = db.query(KBVersion).filter(
        KBVersion.id == version_id,
        KBVersion.knowledge_base_id == kb_id
    ).first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    from .models import KnowledgeBase

    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    return {
        "snapshot_version": snapshot.version_number,
        "snapshot_documents": snapshot.document_count,
        "snapshot_chunks": snapshot.chunk_count,
        "current_documents": kb.document_count if kb else 0,
        "current_chunks": kb.chunk_count if kb else 0,
        "document_diff": (kb.document_count - snapshot.document_count) if kb else 0,
        "chunk_diff": (kb.chunk_count - snapshot.chunk_count) if kb else 0
    }
