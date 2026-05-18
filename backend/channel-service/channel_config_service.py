"""
Channel Differentiation Service

Support for channel-specific configurations:
- Different robot personas for different channels
- Custom welcome messages
- Channel-specific knowledge base associations
- Feature toggles per channel
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .database import get_db_context
from .channel_config_models import (
    ChannelPersona,
    ChannelKnowledgeBaseMapping,
    ChannelFeatureToggle,
    ChannelQuickReply
)


class ChannelConfigService:
    """Service for managing channel-specific configurations"""
    
    def get_channel_persona(
        self,
        enterprise_id: str,
        channel_account_id: str,
        db: Session = None
    ) -> Optional[ChannelPersona]:
        """
        Get persona configuration for a channel
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            db: Database session
        
        Returns:
            ChannelPersona or None
        """
        if db is None:
            with get_db_context() as db:
                return self.get_channel_persona(enterprise_id, channel_account_id, db)
        
        return db.query(ChannelPersona)\
            .filter(
                ChannelPersona.enterprise_id == enterprise_id,
                ChannelPersona.channel_account_id == channel_account_id,
                ChannelPersona.is_active == True
            )\
            .first()
    
    def create_or_update_persona(
        self,
        enterprise_id: str,
        channel_account_id: str,
        persona_name: str,
        greeting_message: str = None,
        farewell_message: str = None,
        fallback_message: str = None,
        language: str = "zh",
        tone: str = "friendly",
        response_length: str = "medium",
        custom_system_prompt: str = None,
        custom_user_prompt: str = None,
        db: Session = None
    ) -> ChannelPersona:
        """
        Create or update channel persona
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            persona_name: Persona name
            greeting_message: Welcome message
            farewell_message: Farewell message
            fallback_message: Fallback message when AI can't answer
            language: Language code
            tone: Tone (friendly, professional, casual, formal)
            response_length: Response length (short, medium, detailed)
            custom_system_prompt: Custom system prompt
            custom_user_prompt: Custom user prompt template
            db: Database session
        
        Returns:
            Created or updated ChannelPersona
        """
        if db is None:
            with get_db_context() as db:
                return self.create_or_update_persona(
                    enterprise_id, channel_account_id, persona_name,
                    greeting_message, farewell_message, fallback_message,
                    language, tone, response_length,
                    custom_system_prompt, custom_user_prompt, db
                )
        
        # Check if persona exists
        existing = db.query(ChannelPersona)\
            .filter(
                ChannelPersona.enterprise_id == enterprise_id,
                ChannelPersona.channel_account_id == channel_account_id
            )\
            .first()
        
        if existing:
            existing.persona_name = persona_name
            existing.greeting_message = greeting_message
            existing.farewell_message = farewell_message
            existing.fallback_message = fallback_message
            existing.language = language
            existing.tone = tone
            existing.response_length = response_length
            existing.custom_system_prompt = custom_system_prompt
            existing.custom_user_prompt = custom_user_prompt
            existing.is_active = True
        else:
            existing = ChannelPersona(
                enterprise_id=enterprise_id,
                channel_account_id=channel_account_id,
                persona_name=persona_name,
                greeting_message=greeting_message,
                farewell_message=farewell_message,
                fallback_message=fallback_message,
                language=language,
                tone=tone,
                response_length=response_length,
                custom_system_prompt=custom_system_prompt,
                custom_user_prompt=custom_user_prompt,
                is_active=True
            )
            db.add(existing)
        
        db.commit()
        db.refresh(existing)
        
        return existing
    
    def get_channel_knowledge_bases(
        self,
        enterprise_id: str,
        channel_account_id: str,
        db: Session = None
    ) -> List[ChannelKnowledgeBaseMapping]:
        """
        Get knowledge bases associated with a channel
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            db: Database session
        
        Returns:
            List of ChannelKnowledgeBaseMapping
        """
        if db is None:
            with get_db_context() as db:
                return self.get_channel_knowledge_bases(enterprise_id, channel_account_id, db)
        
        return db.query(ChannelKnowledgeBaseMapping)\
            .filter(
                ChannelKnowledgeBaseMapping.enterprise_id == enterprise_id,
                ChannelKnowledgeBaseMapping.channel_account_id == channel_account_id,
                ChannelKnowledgeBaseMapping.is_active == True
            )\
            .order_by(ChannelKnowledgeBaseMapping.priority)\
            .all()
    
    def add_knowledge_base_to_channel(
        self,
        enterprise_id: str,
        channel_account_id: str,
        knowledge_base_id: str,
        priority: int = 1,
        db: Session = None
    ) -> ChannelKnowledgeBaseMapping:
        """
        Associate a knowledge base with a channel
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            knowledge_base_id: Knowledge base ID
            priority: Priority (higher = checked first)
            db: Database session
        
        Returns:
            Created ChannelKnowledgeBaseMapping
        """
        if db is None:
            with get_db_context() as db:
                return self.add_knowledge_base_to_channel(
                    enterprise_id, channel_account_id, knowledge_base_id, priority, db
                )
        
        mapping = ChannelKnowledgeBaseMapping(
            enterprise_id=enterprise_id,
            channel_account_id=channel_account_id,
            knowledge_base_id=knowledge_base_id,
            priority=priority,
            is_active=True
        )
        
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        
        return mapping
    
    def remove_knowledge_base_from_channel(
        self,
        enterprise_id: str,
        channel_account_id: str,
        knowledge_base_id: str,
        db: Session = None
    ) -> bool:
        """
        Remove knowledge base association from channel
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            knowledge_base_id: Knowledge base ID
            db: Database session
        
        Returns:
            True if removed, False if not found
        """
        if db is None:
            with get_db_context() as db:
                return self.remove_knowledge_base_from_channel(
                    enterprise_id, channel_account_id, knowledge_base_id, db
                )
        
        mapping = db.query(ChannelKnowledgeBaseMapping)\
            .filter(
                ChannelKnowledgeBaseMapping.enterprise_id == enterprise_id,
                ChannelKnowledgeBaseMapping.channel_account_id == channel_account_id,
                ChannelKnowledgeBaseMapping.knowledge_base_id == knowledge_base_id
            )\
            .first()
        
        if mapping:
            mapping.is_active = False
            db.commit()
            return True
        
        return False
    
    def get_feature_toggle(
        self,
        enterprise_id: str,
        channel_account_id: str,
        feature_name: str,
        db: Session = None
    ) -> Optional[ChannelFeatureToggle]:
        """
        Get feature toggle status for a channel
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            feature_name: Feature name
            db: Database session
        
        Returns:
            ChannelFeatureToggle or None
        """
        if db is None:
            with get_db_context() as db:
                return self.get_feature_toggle(enterprise_id, channel_account_id, feature_name, db)
        
        return db.query(ChannelFeatureToggle)\
            .filter(
                ChannelFeatureToggle.enterprise_id == enterprise_id,
                ChannelFeatureToggle.channel_account_id == channel_account_id,
                ChannelFeatureToggle.feature_name == feature_name
            )\
            .first()
    
    def set_feature_toggle(
        self,
        enterprise_id: str,
        channel_account_id: str,
        feature_name: str,
        is_enabled: bool,
        configuration: Dict = None,
        db: Session = None
    ) -> ChannelFeatureToggle:
        """
        Set feature toggle for a channel
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            feature_name: Feature name
            is_enabled: Whether to enable the feature
            configuration: Feature configuration
            db: Database session
        
        Returns:
            Created or updated ChannelFeatureToggle
        """
        if db is None:
            with get_db_context() as db:
                return self.set_feature_toggle(
                    enterprise_id, channel_account_id, feature_name, is_enabled, configuration, db
                )
        
        existing = db.query(ChannelFeatureToggle)\
            .filter(
                ChannelFeatureToggle.enterprise_id == enterprise_id,
                ChannelFeatureToggle.channel_account_id == channel_account_id,
                ChannelFeatureToggle.feature_name == feature_name
            )\
            .first()
        
        if existing:
            existing.is_enabled = is_enabled
            existing.configuration = configuration
        else:
            existing = ChannelFeatureToggle(
                enterprise_id=enterprise_id,
                channel_account_id=channel_account_id,
                feature_name=feature_name,
                is_enabled=is_enabled,
                configuration=configuration
            )
            db.add(existing)
        
        db.commit()
        db.refresh(existing)
        
        return existing
    
    def get_quick_replies(
        self,
        enterprise_id: str,
        channel_account_id: str,
        db: Session = None
    ) -> List[ChannelQuickReply]:
        """
        Get quick replies for a channel
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            db: Database session
        
        Returns:
            List of ChannelQuickReply
        """
        if db is None:
            with get_db_context() as db:
                return self.get_quick_replies(enterprise_id, channel_account_id, db)
        
        return db.query(ChannelQuickReply)\
            .filter(
                ChannelQuickReply.enterprise_id == enterprise_id,
                ChannelQuickReply.channel_account_id == channel_account_id,
                ChannelQuickReply.is_active == True
            )\
            .order_by(ChannelQuickReply.priority)\
            .all()
    
    def create_quick_reply(
        self,
        enterprise_id: str,
        channel_account_id: str,
        title: str,
        content: str,
        keywords: List[str] = None,
        priority: int = 1,
        db: Session = None
    ) -> ChannelQuickReply:
        """
        Create a quick reply for a channel
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            title: Quick reply title
            content: Quick reply content
            keywords: Trigger keywords
            priority: Priority
            db: Database session
        
        Returns:
            Created ChannelQuickReply
        """
        if db is None:
            with get_db_context() as db:
                return self.create_quick_reply(
                    enterprise_id, channel_account_id, title, content, keywords, priority, db
                )
        
        quick_reply = ChannelQuickReply(
            enterprise_id=enterprise_id,
            channel_account_id=channel_account_id,
            title=title,
            content=content,
            keywords=keywords or [],
            priority=priority,
            is_active=True
        )
        
        db.add(quick_reply)
        db.commit()
        db.refresh(quick_reply)
        
        return quick_reply
    
    def get_channel_configuration(
        self,
        enterprise_id: str,
        channel_account_id: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get complete configuration for a channel
        
        Args:
            enterprise_id: Enterprise ID
            channel_account_id: Channel account ID
            db: Database session
        
        Returns:
            Complete channel configuration dictionary
        """
        if db is None:
            with get_db_context() as db:
                return self.get_channel_configuration(enterprise_id, channel_account_id, db)
        
        persona = self.get_channel_persona(enterprise_id, channel_account_id, db)
        kbs = self.get_channel_knowledge_bases(enterprise_id, channel_account_id, db)
        quick_replies = self.get_quick_replies(enterprise_id, channel_account_id, db)
        
        return {
            "persona": {
                "persona_name": persona.persona_name if persona else None,
                "greeting_message": persona.greeting_message if persona else None,
                "farewell_message": persona.farewell_message if persona else None,
                "fallback_message": persona.fallback_message if persona else None,
                "language": persona.language if persona else "zh",
                "tone": persona.tone if persona else "friendly",
                "response_length": persona.response_length if persona else "medium",
                "custom_system_prompt": persona.custom_system_prompt if persona else None,
                "custom_user_prompt": persona.custom_user_prompt if persona else None
            },
            "knowledge_bases": [
                {
                    "knowledge_base_id": kb.knowledge_base_id,
                    "priority": kb.priority
                }
                for kb in kbs
            ],
            "quick_replies": [
                {
                    "id": qr.id,
                    "title": qr.title,
                    "content": qr.content,
                    "keywords": qr.keywords,
                    "priority": qr.priority
                }
                for qr in quick_replies
            ]
        }


# Singleton instance
_channel_config_service: Optional[ChannelConfigService] = None


def get_channel_config_service() -> ChannelConfigService:
    """Get singleton instance of ChannelConfigService"""
    global _channel_config_service
    if _channel_config_service is None:
        _channel_config_service = ChannelConfigService()
    return _channel_config_service
