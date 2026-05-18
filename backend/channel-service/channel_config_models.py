"""
Channel Differentiation Configuration Models

Support for channel-specific configurations:
- Different robot personas for different channels
- Custom welcome messages
- Channel-specific knowledge base associations
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class ChannelPersona(Base):
    """Channel-specific robot persona configuration"""
    __tablename__ = "channel_personas"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    enterprise_id = Column(String(128), nullable=False, index=True)
    channel_account_id = Column(String(36), nullable=False, index=True)
    
    persona_name = Column(String(128), nullable=False)
    persona_description = Column(Text, nullable=True)
    
    # Persona settings
    greeting_message = Column(Text, nullable=True)
    farewell_message = Column(Text, nullable=True)
    fallback_message = Column(Text, nullable=True)
    
    # Language and tone settings
    language = Column(String(32), default="zh")
    tone = Column(String(32), default="friendly")  # friendly, professional, casual, formal
    
    # Response style
    response_length = Column(String(32), default="medium")  # short, medium, detailed
    
    # Custom prompts
    custom_system_prompt = Column(Text, nullable=True)
    custom_user_prompt = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChannelPersona {self.persona_name} for {self.channel_account_id}>"


class ChannelKnowledgeBaseMapping(Base):
    """Mapping of knowledge bases to channels"""
    __tablename__ = "channel_kb_mappings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    enterprise_id = Column(String(128), nullable=False, index=True)
    channel_account_id = Column(String(36), nullable=False, index=True)
    knowledge_base_id = Column(String(128), nullable=False, index=True)
    
    priority = Column(Integer, default=1)  # Higher priority = checked first
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChannelKBMapping {self.channel_account_id} -> {self.knowledge_base_id}>"


class ChannelFeatureToggle(Base):
    """Feature toggles per channel"""
    __tablename__ = "channel_feature_toggles"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    enterprise_id = Column(String(128), nullable=False, index=True)
    channel_account_id = Column(String(36), nullable=False, index=True)
    
    feature_name = Column(String(128), nullable=False)
    is_enabled = Column(Boolean, default=False)
    configuration = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChannelFeatureToggle {self.feature_name}: {self.is_enabled}>"


class ChannelQuickReply(Base):
    """Quick reply templates for channels"""
    __tablename__ = "channel_quick_replies"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    enterprise_id = Column(String(128), nullable=False, index=True)
    channel_account_id = Column(String(36), nullable=False, index=True)
    
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=True)  # List of trigger keywords
    
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChannelQuickReply {self.title}>"
