"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


# ============ User Schemas ============

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=6, max_length=100)
    enterprise_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    role: str
    enterprise_id: Optional[UUID] = None
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Auth Schemas ============

class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


# ============ Enterprise Schemas ============

class EnterpriseBase(BaseModel):
    """Base enterprise schema"""
    name: str = Field(..., min_length=1, max_length=100)


class EnterpriseCreate(EnterpriseBase):
    """Schema for creating an enterprise"""
    qwen_model: Optional[str] = "qwen-turbo"
    sensitive_words: Optional[List[str]] = []


class SemanticRule(BaseModel):
    """Semantic detection rule"""
    id: Optional[str] = None
    category: str = "custom"
    description: str = ""
    keywords: List[str] = []
    enabled: bool = True
    requires_human: bool = True


class SensitiveSettings(BaseModel):
    """Enterprise sensitive content settings"""
    enable_semantic_detection: bool = True
    enable_keyword_detection: bool = True
    human_required_categories: List[str] = ["legal", "financial", "complaint"]
    semantic_rules: List[SemanticRule] = []
    sensitivity_threshold: float = 0.7
    auto_escalation_enabled: bool = True


class EnterpriseUpdate(BaseModel):
    """Schema for updating an enterprise"""
    name: Optional[str] = None
    qwen_model: Optional[str] = None
    sensitive_words: Optional[List[str]] = None
    settings: Optional[dict] = None
    sensitive_settings: Optional[SensitiveSettings] = None


class EnterpriseResponse(EnterpriseBase):
    """Schema for enterprise response"""
    id: UUID
    api_key: Optional[str] = None
    qwen_model: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Knowledge Base Schemas ============

class KnowledgeBaseBase(BaseModel):
    """Base knowledge base schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """Schema for creating a knowledge base"""
    enterprise_id: UUID


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating a knowledge base"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    """Schema for knowledge base response"""
    id: UUID
    enterprise_id: UUID
    is_active: bool
    document_count: int
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Document Schemas ============

class DocumentBase(BaseModel):
    """Base document schema"""
    filename: str


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: UUID
    knowledge_base_id: UUID
    file_size: int
    file_type: str
    chunk_count: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    document_id: UUID
    filename: str
    status: str
    message: str


# ============ Chat Schemas ============

class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session"""
    title: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: UUID
    user_id: UUID
    enterprise_id: UUID
    title: Optional[str] = None
    is_active: bool
    message_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SourceReference(BaseModel):
    """Source reference for RAG"""
    document_id: UUID
    chunk_id: str
    content: str
    score: float


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message"""
    content: str = Field(..., min_length=1, max_length=5000)


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: UUID
    session_id: UUID
    role: str
    content: str
    sources: List[SourceReference] = []
    is_sensitive: bool
    requires_human: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Schema for chat response"""
    message: ChatMessageResponse
    requires_human: bool
    is_sensitive: bool


# ============ Alert Schemas ============

class AlertResponse(BaseModel):
    """Schema for alert response"""
    id: UUID
    user_id: UUID
    session_id: UUID
    message_id: Optional[UUID] = None
    alert_type: str
    trigger_word: Optional[str] = None
    content: Optional[str] = None
    priority: str
    status: str
    assigned_to: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    """Schema for updating an alert"""
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    resolution_notes: Optional[str] = None


class AlertStats(BaseModel):
    """Alert statistics"""
    total: int
    pending: int
    acknowledged: int
    resolved: int
    by_priority: dict
    by_type: dict


# ============ Common Schemas ============

class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True
