"""
渠道接入层 - Channel Service
统一消息协议、OneID、多渠道适配、差异化渲染
"""
from .config import settings
from .protocols import (
    UnifiedMessage, PlatformMessage, RenderedMessage,
    PlatformType, MessageDirection, MessageContentType
)
from .models import OneIDMapping, ChannelConfig, MessageRoute, PlatformSession
from .adapters import (
    BaseChannelAdapter, get_adapter,
    WechatAdapter, DouyinAdapter, DingtalkAdapter,
    FeishuAdapter, SmsAdapter, WebAdapter
)
from .renderers import get_renderer, render_message
from .oneid import OneIDService, SessionMappingService

__version__ = "1.0.0"
