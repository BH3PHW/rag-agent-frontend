"""
Human Takeover Service
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from .database import get_db_context
from .models import Alert
from .emotion_recognizer import EmotionRecognizer


class HumanTakeoverService:
    """Service for managing human takeover of conversations"""
    
    def __init__(self):
        self.emotion_recognizer = EmotionRecognizer()
    
    def check_takeover_needed(
        self,
        user_id: UUID,
        session_id: UUID,
        message: str,
        conversation_history: List[Dict],
        enterprise_id: UUID,
        retrieval_score: float = None,
        consecutive_failures: int = 0
    ) -> Dict[str, Any]:
        """
        Check if human takeover is needed
        
        Args:
            user_id: User ID
            session_id: Session ID
            message: Current user message
            conversation_history: Full conversation history
            enterprise_id: Enterprise ID
            retrieval_score: RAG retrieval confidence score
            consecutive_failures: Number of consecutive failures
        
        Returns:
            Dict with takeover decision and reason
        """
        reasons = []
        should_takeover = False
        
        # 1. 情绪检测
        emotion_result = self.emotion_recognizer.analyze_emotion(message)
        if emotion_result['requires_human']:
            reasons.append(f"检测到强烈负面情绪: {emotion_result['dominant_emotion']}")
            should_takeover = True
        
        # 2. 检测对话历史中的挫折信号
        if self.emotion_recognizer.detect_frustration_signals(conversation_history):
            reasons.append("用户连续追问，可能对AI回答不满")
            should_takeover = True
        
        # 3. 检索置信度低
        if retrieval_score is not None and retrieval_score < 0.5:
            reasons.append(f"检索置信度过低: {retrieval_score}")
            should_takeover = True
        
        # 4. 连续失败次数过多
        if consecutive_failures >= 3:
            reasons.append(f"连续失败{consecutive_failures}次")
            should_takeover = True
        
        # 5. 用户明确要求转人工
        if any(keyword in message for keyword in ['转人工', '人工客服', '找客服', '人工服务']):
            reasons.append("用户明确要求转人工")
            should_takeover = True
        
        # 6. 检测到敏感话题
        sensitive_topics = ['投诉', '法律', '隐私', '退款', '赔偿', '威胁']
        if any(topic in message for topic in sensitive_topics):
            reasons.append("检测到敏感话题")
            should_takeover = True
        
        return {
            'should_takeover': should_takeover,
            'reasons': reasons,
            'emotion_analysis': emotion_result,
            'retrieval_score': retrieval_score,
            'consecutive_failures': consecutive_failures
        }
    
    def create_takeover_alert(
        self,
        user_id: UUID,
        session_id: UUID,
        enterprise_id: UUID,
        message_id: UUID = None,
        content: str = None,
        reasons: List[str] = None,
        db: Session = None
    ) -> Alert:
        """
        Create a takeover alert and ticket
        
        Args:
            user_id: User ID
            session_id: Session ID
            enterprise_id: Enterprise ID
            message_id: Message ID that triggered takeover
            content: Content that triggered takeover
            reasons: List of reasons for takeover
            db: Database session
        
        Returns:
            Created Alert object
        """
        if db is None:
            with get_db_context() as db:
                return self.create_takeover_alert(
                    user_id, session_id, enterprise_id, message_id, content, reasons, db
                )
        
        alert = Alert(
            user_id=user_id,
            session_id=session_id,
            message_id=message_id,
            enterprise_id=enterprise_id,
            alert_type="HUMAN_TAKEOVER",
            content=content,
            priority="high" if reasons and len(reasons) > 1 else "medium",
            status="pending"
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return alert
    
    def assign_to_agent(
        self,
        alert_id: UUID,
        agent_id: UUID,
        db: Session = None
    ) -> Alert:
        """
        Assign alert to a human agent
        
        Args:
            alert_id: Alert ID
            agent_id: Agent user ID
            db: Database session
        
        Returns:
            Updated Alert object
        """
        if db is None:
            with get_db_context() as db:
                return self.assign_to_agent(alert_id, agent_id, db)
        
        alert = db.query(Alert)\
            .filter(Alert.id == alert_id)\
            .first()
        
        if not alert:
            raise ValueError("Alert not found")
        
        alert.assigned_to = agent_id
        alert.status = "assigned"
        
        db.commit()
        db.refresh(alert)
        
        return alert
    
    def acknowledge_alert(
        self,
        alert_id: UUID,
        db: Session = None
    ) -> Alert:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert ID
            db: Database session
        
        Returns:
            Updated Alert object
        """
        if db is None:
            with get_db_context() as db:
                return self.acknowledge_alert(alert_id, db)
        
        alert = db.query(Alert)\
            .filter(Alert.id == alert_id)\
            .first()
        
        if not alert:
            raise ValueError("Alert not found")
        
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        
        db.commit()
        db.refresh(alert)
        
        return alert
    
    def resolve_alert(
        self,
        alert_id: UUID,
        resolution_notes: str = None,
        db: Session = None
    ) -> Alert:
        """
        Resolve an alert
        
        Args:
            alert_id: Alert ID
            resolution_notes: Resolution notes
            db: Database session
        
        Returns:
            Updated Alert object
        """
        if db is None:
            with get_db_context() as db:
                return self.resolve_alert(alert_id, resolution_notes, db)
        
        alert = db.query(Alert)\
            .filter(Alert.id == alert_id)\
            .first()
        
        if not alert:
            raise ValueError("Alert not found")
        
        alert.status = "resolved"
        alert.resolution_notes = resolution_notes
        alert.resolved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(alert)
        
        return alert


# Singleton instance
_human_takeover_service: Optional[HumanTakeoverService] = None


def get_human_takeover_service() -> HumanTakeoverService:
    """Get singleton instance of HumanTakeoverService"""
    global _human_takeover_service
    if _human_takeover_service is None:
        _human_takeover_service = HumanTakeoverService()
    return _human_takeover_service
