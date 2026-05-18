"""
User Feedback Service

Handles user feedback (thumbs up/down) for RLHF data collection.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .database import get_db_context
from .quality_models import Feedback, UnmatchedQuestion
from .models import ChatMessage


class FeedbackService:
    """Service for managing user feedback"""
    
    def create_feedback(
        self,
        message_id: UUID,
        user_id: UUID,
        rating: str,
        reason: str = None,
        db: Session = None
    ) -> Feedback:
        """
        Create user feedback (thumbs up/down)
        
        Args:
            message_id: The message ID being rated
            user_id: The user providing feedback
            rating: "thumbs_up" or "thumbs_down"
            reason: Optional reason for thumbs down
            db: Database session
        
        Returns:
            Created Feedback object
        """
        if db is None:
            with get_db_context() as db:
                return self.create_feedback(message_id, user_id, rating, reason, db)
        
        # Check if feedback already exists for this message
        existing = db.query(Feedback)\
            .filter(Feedback.message_id == message_id)\
            .first()
        
        if existing:
            # Update existing feedback
            existing.rating = rating
            existing.reason = reason
        else:
            existing = Feedback(
                message_id=message_id,
                user_id=user_id,
                rating=rating,
                reason=reason
            )
            db.add(existing)
        
        db.commit()
        db.refresh(existing)
        
        return existing
    
    def get_feedback(
        self,
        message_id: UUID,
        db: Session = None
    ) -> Optional[Feedback]:
        """
        Get feedback for a specific message
        
        Args:
            message_id: The message ID
            db: Database session
        
        Returns:
            Feedback object or None
        """
        if db is None:
            with get_db_context() as db:
                return self.get_feedback(message_id, db)
        
        return db.query(Feedback)\
            .filter(Feedback.message_id == message_id)\
            .first()
    
    def get_feedback_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        db: Session = None
    ) -> List[Feedback]:
        """
        Get feedback submitted by a specific user
        
        Args:
            user_id: The user ID
            limit: Maximum number of results
            db: Database session
        
        Returns:
            List of Feedback objects
        """
        if db is None:
            with get_db_context() as db:
                return self.get_feedback_by_user(user_id, limit, db)
        
        return db.query(Feedback)\
            .filter(Feedback.user_id == user_id)\
            .order_by(desc(Feedback.created_at))\
            .limit(limit)\
            .all()
    
    def get_negative_feedback(
        self,
        limit: int = 100,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Get all negative feedback with message details
        
        Args:
            limit: Maximum number of results
            db: Database session
        
        Returns:
            List of feedback with associated message content
        """
        if db is None:
            with get_db_context() as db:
                return self.get_negative_feedback(limit, db)
        
        # Join with ChatMessage to get the actual message content
        feedback_with_messages = db.query(Feedback, ChatMessage)\
            .join(ChatMessage, Feedback.message_id == ChatMessage.id)\
            .filter(Feedback.rating == "thumbs_down")\
            .order_by(desc(Feedback.created_at))\
            .limit(limit)\
            .all()
        
        results = []
        for feedback, message in feedback_with_messages:
            results.append({
                "feedback_id": str(feedback.id),
                "message_id": str(feedback.message_id),
                "user_id": str(feedback.user_id),
                "rating": feedback.rating,
                "reason": feedback.reason,
                "message_content": message.content,
                "created_at": feedback.created_at.isoformat()
            })
        
        return results
    
    def get_feedback_stats(
        self,
        enterprise_id: UUID = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get feedback statistics
        
        Args:
            enterprise_id: Optional enterprise filter
            db: Database session
        
        Returns:
            Statistics dictionary
        """
        if db is None:
            with get_db_context() as db:
                return self.get_feedback_stats(enterprise_id, db)
        
        all_feedback = db.query(Feedback).all()
        
        stats = {
            "total": len(all_feedback),
            "thumbs_up": len([f for f in all_feedback if f.rating == "thumbs_up"]),
            "thumbs_down": len([f for f in all_feedback if f.rating == "thumbs_down"]),
            "positive_rate": 0.0
        }
        
        if stats["total"] > 0:
            stats["positive_rate"] = stats["thumbs_up"] / stats["total"]
        
        return stats
    
    def export_feedback_for_finetuning(
        self,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Export feedback data for LLM fine-tuning (RLHF format)
        
        Args:
            db: Database session
        
        Returns:
            List of feedback in RLHF format
        """
        if db is None:
            with get_db_context() as db:
                return self.export_feedback_for_finetuning(db)
        
        # Get negative feedback with message context
        negative_feedback = self.get_negative_feedback(limit=1000, db=db)
        
        # Format for RLHF training
        rlhf_data = []
        for feedback in negative_feedback:
            rlhf_data.append({
                "prompt": feedback["message_content"],
                "chosen": None,  # Would be filled with human-corrected answer
                "rejected": feedback["message_content"],
                "feedback_reason": feedback["reason"],
                "created_at": feedback["created_at"]
            })
        
        return rlhf_data


# Singleton instance
_feedback_service: Optional[FeedbackService] = None


def get_feedback_service() -> FeedbackService:
    """Get singleton instance of FeedbackService"""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
