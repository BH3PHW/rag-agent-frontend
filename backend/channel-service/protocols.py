"""
渠道接入层 - 统一消息协议
定义内部统一消息格式，所有渠道消息转换为该格式
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class PlatformType(str, Enum):
    """支持的平台类型"""
    WEB = "web"
    WECHAT = "wechat"
    WECHAT_MINIPROGRAM = "wechat_miniprogram"
    DOUYIN = "douyin"
    DINGTALK = "dingtalk"
    FEISHU = "feishu"
    SMS = "sms"
    EMAIL = "email"
    UNKNOWN = "unknown"


class MessageDirection(str, Enum):
    """消息方向"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageContentType(str, Enum):
    """消息内容类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    LOCATION = "location"
    LINK = "link"
    CARD = "card"


class UnifiedMessage(BaseModel):
    """内部统一消息格式
    
    无论外部传来什么格式，最终都转换为这个标准格式
    """
    message_id: str = Field(..., description="消息唯一ID")
    
    enterprise_id: str = Field(..., description="企业ID")
    
    unified_user_id: Optional[str] = Field(None, description="统一用户ID（OneID）")
    
    platform_type: PlatformType = Field(..., description="平台类型")
    platform_user_id: str = Field(..., description="平台用户ID")
    
    platform_session_id: Optional[str] = Field(None, description="平台会话ID")
    chat_session_id: Optional[str] = Field(None, description="内部聊天会话ID")
    
    direction: MessageDirection = Field(MessageDirection.INBOUND, description="消息方向")
    
    content_type: MessageContentType = Field(MessageContentType.TEXT, description="内容类型")
    
    content: str = Field(..., description="消息内容（文本内容或资源引用）")
    
    media_url: Optional[str] = Field(None, description="媒体资源URL")
    media_type: Optional[str] = Field(None, description="媒体类型")
    
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="额外数据")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")
    
    original_message: Optional[Dict[str, Any]] = Field(None, description="原始消息")
    
    class Config:
        use_enum_values = True


class PlatformMessage(BaseModel):
    """平台原生消息格式"""
    platform_type: PlatformType
    raw_data: Any
    enterprise_id: str
    extra_config: Dict[str, Any] = Field(default_factory=dict)


class RenderedMessage(BaseModel):
    """渲染后的平台消息"""
    platform_type: PlatformType
    content: Any
    message_type: str
    extra_data: Dict[str, Any] = Field(default_factory=dict)
