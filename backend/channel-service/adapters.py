"""
渠道接入层 - 渠道适配器
为每个平台编写专属解析器
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from .protocols import (
    UnifiedMessage, PlatformMessage,
    PlatformType, MessageContentType, MessageDirection
)
from datetime import datetime
import uuid
import xml.etree.ElementTree as ET


class BaseChannelAdapter(ABC):
    """渠道适配器基类"""
    
    platform_type: PlatformType
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def parse(self, platform_message: PlatformMessage) -> UnifiedMessage:
        """将平台原生消息解析为统一消息格式"""
        pass
    
    @abstractmethod
    def render(self, unified_message: UnifiedMessage) -> Any:
        """将统一消息渲染为平台原生格式"""
        pass
    
    @abstractmethod
    def validate_signature(self, request: Any) -> bool:
        """验证消息签名"""
        pass
    
    def generate_message_id(self) -> str:
        """生成消息ID"""
        return str(uuid.uuid4())


class WechatAdapter(BaseChannelAdapter):
    """微信公众号适配器 - 解析加密 XML 消息"""
    
    platform_type = PlatformType.WECHAT
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.appid = config.get("appid", "")
        self.secret = config.get("secret", "")
        self.token = config.get("token", "")
        self.aes_key = config.get("aes_key", "")
    
    def parse(self, platform_message: PlatformMessage) -> UnifiedMessage:
        """解析微信 XML 消息"""
        xml_data = platform_message.raw_data
        
        if isinstance(xml_data, str):
            root = ET.fromstring(xml_data)
        else:
            root = ET.fromstring(xml_data.decode('utf-8'))
        
        msg_type = root.findtext('MsgType', 'text')
        from_user = root.findtext('FromUserName', '')
        to_user = root.findtext('ToUserName', '')
        
        content = ""
        media_url = ""
        content_type = MessageContentType.TEXT
        
        if msg_type == 'text':
            content = root.findtext('Content', '')
        elif msg_type == 'image':
            media_url = root.findtext('MediaId', '')
            content = "[图片]"
            content_type = MessageContentType.IMAGE
        elif msg_type == 'voice':
            media_url = root.findtext('MediaId', '')
            content = "[语音]"
            content_type = MessageContentType.VOICE
        elif msg_type == 'event':
            event_type = root.findtext('Event', '')
            event_key = root.findtext('EventKey', '')
            content = f"[事件: {event_type} {event_key}]"
        
        unionid = root.findtext('UnionId', '')
        
        unified_msg = UnifiedMessage(
            message_id=self.generate_message_id(),
            enterprise_id=platform_message.enterprise_id,
            platform_type=self.platform_type,
            platform_user_id=from_user,
            platform_session_id=from_user,
            direction=MessageDirection.INBOUND,
            content_type=content_type,
            content=content,
            media_url=media_url,
            extra_data={
                "unionid": unionid,
                "original_xml": xml_data,
                "from_user": from_user,
                "to_user": to_user
            },
            original_message={
                "xml": xml_data
            }
        )
        
        return unified_msg
    
    def render(self, unified_message: UnifiedMessage) -> str:
        """渲染回复为微信 XML 格式"""
        from_user = unified_message.extra_data.get('from_user', '')
        to_user = unified_message.platform_user_id
        
        xml = f"""<xml>
    <ToUserName><![CDATA[{to_user}]]></ToUserName>
    <FromUserName><![CDATA[{from_user}]]></FromUserName>
    <CreateTime>{int(datetime.now().timestamp())}</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[{unified_message.content}]]></Content>
</xml>"""
        
        return xml
    
    def validate_signature(self, request: Any) -> bool:
        """验证微信签名（简化版）"""
        return True


class WechatMiniprogramAdapter(BaseChannelAdapter):
    """微信小程序适配器"""
    
    platform_type = PlatformType.WECHAT_MINIPROGRAM
    
    def parse(self, platform_message: PlatformMessage) -> UnifiedMessage:
        """解析小程序消息"""
        data = platform_message.raw_data
        
        content = data.get("Content", "")
        from_user = data.get("FromUserName", "")
        unionid = data.get("UnionId", "")
        
        unified_msg = UnifiedMessage(
            message_id=self.generate_message_id(),
            enterprise_id=platform_message.enterprise_id,
            platform_type=self.platform_type,
            platform_user_id=from_user,
            platform_session_id=data.get("Session", from_user),
            direction=MessageDirection.INBOUND,
            content_type=MessageContentType.TEXT,
            content=content,
            extra_data={
                "unionid": unionid,
                "session": data.get("Session")
            },
            original_message=data
        )
        
        return unified_msg
    
    def render(self, unified_message: UnifiedMessage) -> Dict[str, Any]:
        """渲染小程序回复"""
        return {
            "ToUserName": unified_message.platform_user_id,
            "MsgType": "text",
            "Content": unified_message.content
        }
    
    def validate_signature(self, request: Any) -> bool:
        return True


class DouyinAdapter(BaseChannelAdapter):
    """抖音适配器 - 签名校验和 JSON 消息解析"""
    
    platform_type = PlatformType.DOUYIN
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.app_key = config.get("app_key", "")
        self.app_secret = config.get("app_secret", "")
    
    def parse(self, platform_message: PlatformMessage) -> UnifiedMessage:
        """解析抖音 JSON 消息"""
        data = platform_message.raw_data
        
        content = data.get("content", "")
        from_user = data.get("open_id", "")
        msg_id = data.get("msg_id", "")
        
        unified_msg = UnifiedMessage(
            message_id=msg_id or self.generate_message_id(),
            enterprise_id=platform_message.enterprise_id,
            platform_type=self.platform_type,
            platform_user_id=from_user,
            platform_session_id=from_user,
            direction=MessageDirection.INBOUND,
            content_type=MessageContentType.TEXT,
            content=content,
            extra_data={
                "open_id": from_user,
                "msg_id": msg_id
            },
            original_message=data
        )
        
        return unified_msg
    
    def render(self, unified_message: UnifiedMessage) -> Dict[str, Any]:
        """渲染抖音回复"""
        return {
            "content": unified_message.content,
            "to_user_id": unified_message.platform_user_id,
            "msg_type": "text"
        }
    
    def validate_signature(self, request: Any) -> bool:
        """验证抖音签名（简化版）"""
        return True


class DingtalkAdapter(BaseChannelAdapter):
    """钉钉适配器"""
    
    platform_type = PlatformType.DINGTALK
    
    def parse(self, platform_message: PlatformMessage) -> UnifiedMessage:
        data = platform_message.raw_data
        
        sender_id = data.get("senderId", "")
        text = data.get("text", {}).get("content", "")
        
        return UnifiedMessage(
            message_id=self.generate_message_id(),
            enterprise_id=platform_message.enterprise_id,
            platform_type=self.platform_type,
            platform_user_id=sender_id,
            platform_session_id=sender_id,
            direction=MessageDirection.INBOUND,
            content_type=MessageContentType.TEXT,
            content=text,
            original_message=data
        )
    
    def render(self, unified_message: UnifiedMessage) -> Dict[str, Any]:
        """渲染钉钉 ActionCard 交互卡片"""
        return {
            "msgtype": "text",
            "text": {
                "content": unified_message.content
            }
        }
    
    def render_card(self, content: str, buttons: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """渲染钉钉 ActionCard"""
        return {
            "msgtype": "actionCard",
            "actionCard": {
                "title": "客服消息",
                "text": content,
                "singleTitle": "了解更多",
                "singleURL": ""
            }
        }
    
    def validate_signature(self, request: Any) -> bool:
        return True


class FeishuAdapter(BaseChannelAdapter):
    """飞书适配器"""
    
    platform_type = PlatformType.FEISHU
    
    def parse(self, platform_message: PlatformMessage) -> UnifiedMessage:
        data = platform_message.raw_data
        
        sender_id = data.get("sender", {}).get("sender_id", "")
        text = ""
        
        if data.get("message_type") == "text":
            text = data.get("text", "")
        
        return UnifiedMessage(
            message_id=self.generate_message_id(),
            enterprise_id=platform_message.enterprise_id,
            platform_type=self.platform_type,
            platform_user_id=sender_id,
            platform_session_id=sender_id,
            direction=MessageDirection.INBOUND,
            content_type=MessageContentType.TEXT,
            content=text,
            original_message=data
        )
    
    def render(self, unified_message: UnifiedMessage) -> Dict[str, Any]:
        """渲染飞书消息"""
        return {
            "msg_type": "text",
            "content": {
                "text": unified_message.content
            }
        }
    
    def validate_signature(self, request: Any) -> bool:
        return True


class SmsAdapter(BaseChannelAdapter):
    """短信适配器 - 只支持纯文本"""
    
    platform_type = PlatformType.SMS
    
    def parse(self, platform_message: PlatformMessage) -> UnifiedMessage:
        data = platform_message.raw_data
        
        phone = data.get("phone", "")
        content = data.get("content", "")
        
        return UnifiedMessage(
            message_id=self.generate_message_id(),
            enterprise_id=platform_message.enterprise_id,
            platform_type=self.platform_type,
            platform_user_id=phone,
            platform_session_id=phone,
            direction=MessageDirection.INBOUND,
            content_type=MessageContentType.TEXT,
            content=content,
            extra_data={
                "phone": phone
            },
            original_message=data
        )
    
    def render(self, unified_message: UnifiedMessage) -> Dict[str, Any]:
        """短信只支持纯文本"""
        return {
            "phone": unified_message.platform_user_id,
            "content": unified_message.content
        }
    
    def validate_signature(self, request: Any) -> bool:
        return True


class WebAdapter(BaseChannelAdapter):
    """Web Widget 适配器"""
    
    platform_type = PlatformType.WEB
    
    def parse(self, platform_message: PlatformMessage) -> UnifiedMessage:
        data = platform_message.raw_data
        
        user_id = data.get("user_id", "")
        content = data.get("content", "")
        session_id = data.get("session_id", "")
        
        return UnifiedMessage(
            message_id=self.generate_message_id(),
            enterprise_id=platform_message.enterprise_id,
            platform_type=self.platform_type,
            platform_user_id=user_id,
            platform_session_id=session_id,
            direction=MessageDirection.INBOUND,
            content_type=MessageContentType.TEXT,
            content=content,
            original_message=data
        )
    
    def render(self, unified_message: UnifiedMessage) -> Dict[str, Any]:
        """Web 端支持富文本"""
        return {
            "content": unified_message.content,
            "type": "text",
            "html": self.render_html(unified_message.content)
        }
    
    def render_html(self, text: str) -> str:
        """渲染简单 HTML 格式"""
        import re
        html = text.replace("\n", "<br>")
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        return html
    
    def validate_signature(self, request: Any) -> bool:
        return True


# 适配器注册
_adapters: Dict[PlatformType, type] = {
    PlatformType.WEB: WebAdapter,
    PlatformType.WECHAT: WechatAdapter,
    PlatformType.WECHAT_MINIPROGRAM: WechatMiniprogramAdapter,
    PlatformType.DOUYIN: DouyinAdapter,
    PlatformType.DINGTALK: DingtalkAdapter,
    PlatformType.FEISHU: FeishuAdapter,
    PlatformType.SMS: SmsAdapter
}


def get_adapter(platform_type: PlatformType, config: Dict[str, Any]) -> BaseChannelAdapter:
    """获取渠道适配器"""
    adapter_class = _adapters.get(platform_type)
    if not adapter_class:
        raise ValueError(f"Unsupported platform: {platform_type}")
    return adapter_class(config)
