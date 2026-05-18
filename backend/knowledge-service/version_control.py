"""
Version Control Service for Knowledge Base

Features:
1. Document version tracking
2. Knowledge base version for gray release
3. Incremental update mechanism
4. Rollback support
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .database import get_db_context
from .models import Document, KnowledgeBase
from .version_models import DocumentVersion, KnowledgeBaseVersion, IncrementalUpdateTask
from .vector_store import get_vector_store
import hashlib


class VersionControlService:
    """Service for managing document and knowledge base versions"""
    
    def __init__(self):
        self.vector_store = get_vector_store()
    
    def create_document_version(
        self,
        document_id: UUID,
        file_hash: str,
        changes: Dict = None,
        db: Session = None
    ) -> DocumentVersion:
        """
        Create a new version for a document
        
        Args:
            document_id: The document ID
            file_hash: SHA256 hash of the file content
            changes: Description of what changed
            db: Database session
        
        Returns:
            The created DocumentVersion
        """
        if db is None:
            with get_db_context() as db:
                return self.create_document_version(document_id, file_hash, changes, db)
        
        # Get current max version number
        max_version = db.query(DocumentVersion.version_number)\
            .filter(DocumentVersion.document_id == document_id)\
            .order_by(desc(DocumentVersion.version_number))\
            .first()
        
        new_version = (max_version[0] + 1) if max_version else 1
        
        version = DocumentVersion(
            document_id=document_id,
            version_number=new_version,
            file_hash=file_hash,
            changes=changes or {},
            status="draft"
        )
        
        db.add(version)
        db.commit()
        db.refresh(version)
        
        return version
    
    def publish_document_version(
        self,
        version_id: UUID,
        db: Session = None
    ) -> DocumentVersion:
        """
        Publish a document version
        
        Args:
            version_id: The version ID to publish
            db: Database session
        
        Returns:
            The published DocumentVersion
        """
        if db is None:
            with get_db_context() as db:
                return self.publish_document_version(version_id, db)
        
        version = db.query(DocumentVersion)\
            .filter(DocumentVersion.id == version_id)\
            .first()
        
        if not version:
            raise ValueError("Version not found")
        
        # Deactivate previous versions
        db.query(DocumentVersion)\
            .filter(DocumentVersion.document_id == version.document_id)\
            .update({"is_active": False})
        
        version.is_active = True
        version.status = "published"
        version.published_at = datetime.utcnow()
        
        db.commit()
        db.refresh(version)
        
        # Trigger incremental update
        self.trigger_incremental_update(version.document_id, db)
        
        return version
    
    def rollback_document_version(
        self,
        document_id: UUID,
        target_version: int,
        db: Session = None
    ) -> DocumentVersion:
        """
        Rollback document to a previous version
        
        Args:
            document_id: The document ID
            target_version: The version number to rollback to
            db: Database session
        
        Returns:
            The rolled-back DocumentVersion
        """
        if db is None:
            with get_db_context() as db:
                return self.rollback_document_version(document_id, target_version, db)
        
        target = db.query(DocumentVersion)\
            .filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == target_version
            )\
            .first()
        
        if not target:
            raise ValueError(f"Version {target_version} not found")
        
        # Deactivate all versions
        db.query(DocumentVersion)\
            .filter(DocumentVersion.document_id == document_id)\
            .update({"is_active": False})
        
        # Create new version based on target
        new_version = DocumentVersion(
            document_id=document_id,
            version_number=target.version_number + 1,
            file_hash=target.file_hash,
            changes={"rollback_to_version": target_version},
            status="published",
            is_active=True,
            published_at=datetime.utcnow()
        )
        
        db.add(new_version)
        db.commit()
        db.refresh(new_version)
        
        # Trigger incremental update
        self.trigger_incremental_update(document_id, db)
        
        return new_version
    
    def create_knowledge_base_version(
        self,
        knowledge_base_id: UUID,
        version_tag: str,
        description: str = None,
        db: Session = None
    ) -> KnowledgeBaseVersion:
        """
        Create a new knowledge base version for gray release
        
        Args:
            knowledge_base_id: The knowledge base ID
            version_tag: Version tag (e.g., "v1.0.0")
            description: Description of changes
            db: Database session
        
        Returns:
            The created KnowledgeBaseVersion
        """
        if db is None:
            with get_db_context() as db:
                return self.create_knowledge_base_version(knowledge_base_id, version_tag, description, db)
        
        # Get all active document versions
        kb_version = KnowledgeBaseVersion(
            knowledge_base_id=knowledge_base_id,
            version_tag=version_tag,
            description=description,
            status="draft",
            traffic_percentage=0
        )
        
        db.add(kb_version)
        db.commit()
        db.refresh(kb_version)
        
        return kb_version
    
    def start_gray_release(
        self,
        kb_version_id: UUID,
        traffic_percentage: int = 10,
        db: Session = None
    ) -> KnowledgeBaseVersion:
        """
        Start gray release with specified traffic percentage
        
        Args:
            kb_version_id: The knowledge base version ID
            traffic_percentage: Percentage of traffic to route (0-100)
            db: Database session
        
        Returns:
            The updated KnowledgeBaseVersion
        """
        if db is None:
            with get_db_context() as db:
                return self.start_gray_release(kb_version_id, traffic_percentage, db)
        
        kb_version = db.query(KnowledgeBaseVersion)\
            .filter(KnowledgeBaseVersion.id == kb_version_id)\
            .first()
        
        if not kb_version:
            raise ValueError("Knowledge base version not found")
        
        kb_version.status = "staging"
        kb_version.traffic_percentage = min(max(0, traffic_percentage), 100)
        
        db.commit()
        db.refresh(kb_version)
        
        return kb_version
    
    def full_release(
        self,
        kb_version_id: UUID,
        db: Session = None
    ) -> KnowledgeBaseVersion:
        """
        Fully release a knowledge base version (100% traffic)
        
        Args:
            kb_version_id: The knowledge base version ID
            db: Database session
        
        Returns:
            The updated KnowledgeBaseVersion
        """
        if db is None:
            with get_db_context() as db:
                return self.full_release(kb_version_id, db)
        
        kb_version = db.query(KnowledgeBaseVersion)\
            .filter(KnowledgeBaseVersion.id == kb_version_id)\
            .first()
        
        if not kb_version:
            raise ValueError("Knowledge base version not found")
        
        kb_version.status = "published"
        kb_version.traffic_percentage = 100
        kb_version.published_at = datetime.utcnow()
        
        # Archive previous published versions
        db.query(KnowledgeBaseVersion)\
            .filter(
                KnowledgeBaseVersion.knowledge_base_id == kb_version.knowledge_base_id,
                KnowledgeBaseVersion.id != kb_version_id,
                KnowledgeBaseVersion.status == "published"
            )\
            .update({"status": "archived"})
        
        db.commit()
        db.refresh(kb_version)
        
        return kb_version
    
    def rollback_knowledge_base(
        self,
        kb_version_id: UUID,
        db: Session = None
    ) -> KnowledgeBaseVersion:
        """
        Rollback knowledge base to previous version
        
        Args:
            kb_version_id: The version to rollback to
            db: Database session
        
        Returns:
            The rolled-back KnowledgeBaseVersion
        """
        if db is None:
            with get_db_context() as db:
                return self.rollback_knowledge_base(kb_version_id, db)
        
        target_version = db.query(KnowledgeBaseVersion)\
            .filter(KnowledgeBaseVersion.id == kb_version_id)\
            .first()
        
        if not target_version:
            raise ValueError("Target version not found")
        
        # Mark current published version as rolled back
        db.query(KnowledgeBaseVersion)\
            .filter(
                KnowledgeBaseVersion.knowledge_base_id == target_version.knowledge_base_id,
                KnowledgeBaseVersion.status == "published"
            )\
            .update({
                "status": "archived",
                "rolled_back_at": datetime.utcnow()
            })
        
        # Publish target version
        target_version.status = "published"
        target_version.traffic_percentage = 100
        target_version.published_at = datetime.utcnow()
        
        db.commit()
        db.refresh(target_version)
        
        return target_version
    
    def trigger_incremental_update(
        self,
        document_id: UUID,
        db: Session = None,
        task_type: str = "update"
    ) -> IncrementalUpdateTask:
        """
        Trigger an incremental update task
        
        Args:
            document_id: The document ID to update
            db: Database session
            task_type: Type of task (create, update, delete, reindex)
        
        Returns:
            The created IncrementalUpdateTask
        """
        if db is None:
            with get_db_context() as db:
                return self.trigger_incremental_update(document_id, db, task_type)
        
        # Get knowledge base from document
        document = db.query(Document)\
            .filter(Document.id == document_id)\
            .first()
        
        if not document:
            raise ValueError("Document not found")
        
        task = IncrementalUpdateTask(
            knowledge_base_id=document.knowledge_base_id,
            document_id=document_id,
            task_type=task_type,
            status="pending"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Process the task (would be async in production)
        self.process_incremental_update(task.id, db)
        
        return task
    
    def process_incremental_update(
        self,
        task_id: UUID,
        db: Session = None
    ) -> None:
        """
        Process an incremental update task
        
        Args:
            task_id: The task ID to process
            db: Database session
        """
        if db is None:
            with get_db_context() as db:
                return self.process_incremental_update(task_id, db)
        
        task = db.query(IncrementalUpdateTask)\
            .filter(IncrementalUpdateTask.id == task_id)\
            .first()
        
        if not task:
            raise ValueError("Task not found")
        
        task.status = "running"
        task.started_at = datetime.utcnow()
        db.commit()
        
        try:
            document = db.query(Document)\
                .filter(Document.id == task.document_id)\
                .first()
            
            if not document:
                raise ValueError("Document not found")
            
            # Get the active version
            active_version = db.query(DocumentVersion)\
                .filter(
                    DocumentVersion.document_id == task.document_id,
                    DocumentVersion.is_active == True
                )\
                .first()
            
            if not active_version:
                raise ValueError("No active version found")
            
            # Update vector store incrementally
            self.vector_store.update_document(document, active_version)
            
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
        
        db.commit()
    
    def get_document_history(
        self,
        document_id: UUID,
        db: Session = None
    ) -> List[DocumentVersion]:
        """
        Get version history for a document
        
        Args:
            document_id: The document ID
            db: Database session
        
        Returns:
            List of DocumentVersion objects
        """
        if db is None:
            with get_db_context() as db:
                return self.get_document_history(document_id, db)
        
        versions = db.query(DocumentVersion)\
            .filter(DocumentVersion.document_id == document_id)\
            .order_by(desc(DocumentVersion.version_number))\
            .all()
        
        return versions
    
    def get_kb_version_history(
        self,
        knowledge_base_id: UUID,
        db: Session = None
    ) -> List[KnowledgeBaseVersion]:
        """
        Get version history for a knowledge base
        
        Args:
            knowledge_base_id: The knowledge base ID
            db: Database session
        
        Returns:
            List of KnowledgeBaseVersion objects
        """
        if db is None:
            with get_db_context() as db:
                return self.get_kb_version_history(knowledge_base_id, db)
        
        versions = db.query(KnowledgeBaseVersion)\
            .filter(KnowledgeBaseVersion.knowledge_base_id == knowledge_base_id)\
            .order_by(desc(KnowledgeBaseVersion.created_at))\
            .all()
        
        return versions


# Singleton instance
_version_control_service: Optional[VersionControlService] = None


def get_version_control_service() -> VersionControlService:
    """Get singleton instance of VersionControlService"""
    global _version_control_service
    if _version_control_service is None:
        _version_control_service = VersionControlService()
    return _version_control_service
