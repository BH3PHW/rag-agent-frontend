"""
渠道接入层 - 差异化消息渲染器
根据不同渠道将 Markdown/文本转换为渠道特定格式
"""
from typing import Dict, Any, List, Optional
from .protocols import UnifiedMessage, PlatformType, RenderedMessage
import re
import json


class BaseRenderer:
    """渲染器基类"""
    
    platform_type: PlatformType
    
    def render(self, msg: UnifiedMessage) -> RenderedMessage:
        """将统一消息渲染为平台格式"""
        raise NotImplementedError


class WechatRenderer(BaseRenderer):
    """微信渲染器 - 纯文本为主"""
    
    platform_type = PlatformType.WECHAT
    
    def render(self, msg: UnifiedMessage) -> RenderedMessage:
        text = self._render_text(msg.content)
        return RenderedMessage(
            platform_type=self.platform_type,
            content=text,
            message_type="text"
        )
    
    def _render_text(self, text: str) -> str:
        """简化文本，移除 Markdown 格式"""
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        return text


class WechatMiniprogramRenderer(BaseRenderer):
    """小程序渲染器"""
    
    platform_type = PlatformType.WECHAT_MINIPROGRAM
    
    def render(self, msg: UnifiedMessage) -> RenderedMessage:
        text = self._render_text(msg.content)
        return RenderedMessage(
            platform_type=self.platform_type,
            content=text,
            message_type="text"
        )
    
    def _render_text(self, text: str) -> str:
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        return text


class WebRenderer(BaseRenderer):
    """Web 渲染器 - 支持富文本和交互式卡片"""
    
    platform_type = PlatformType.WEB
    
    def render(self, msg: UnifiedMessage) -> RenderedMessage:
        html = self._render_html(msg.content)
        
        return RenderedMessage(
            platform_type=self.platform_type,
            content={
                "text": msg.content,
                "html": html
            },
            message_type="text",
            extra_data={"has_html": True}
        )
    
    def _render_html(self, text: str) -> str:
        """Markdown 转简单 HTML"""
        html = text
        
        html = html.replace("\n", "<br>")
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', html)
        
        return html
    
    def render_card(self, title: str, content: str, buttons: List[Dict[str, Any]]) -> RenderedMessage:
        """渲染交互卡片"""
        return RenderedMessage(
            platform_type=self.platform_type,
            content={
                "title": title,
                "content": content,
                "buttons": buttons
            },
            message_type="card"
        )


class DouyinRenderer(BaseRenderer):
    """抖音渲染器"""
    
    platform_type = PlatformType.DOUYIN
    
    def render(self, msg: UnifiedMessage) -> RenderedMessage:
        text = self._render_text(msg.content)
        return RenderedMessage(
            platform_type=self.platform_type,
            content=text,
            message_type="text"
        )
    
    def _render_text(self, text: str) -> str:
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        return text


class DingtalkRenderer(BaseRenderer):
    """钉钉渲染器 - 支持 ActionCard 交互卡片"""
    
    platform_type = PlatformType.DINGTALK
    
    def render(self, msg: UnifiedMessage) -> RenderedMessage:
        if self._is_complex(msg.content):
            content = self._render_action_card(msg.content)
            msg_type = "actionCard"
        else:
            text = self._render_text(msg.content)
            content = {"content": text}
            msg_type = "text"
        
        return RenderedMessage(
            platform_type=self.platform_type,
            content=content,
            message_type=msg_type
        )
    
    def _render_text(self, text: str) -> str:
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        return text
    
    def _is_complex(self, text: str) -> bool:
        """判断是否需要复杂卡片"""
        return len(text) > 200 or '\n' in text or '链接' in text
    
    def _render_action_card(self, text: str) -> Dict[str, Any]:
        """渲染 ActionCard"""
        return {
            "msgtype": "actionCard",
            "actionCard": {
                "title": "客服消息",
                "text": self._render_text(text),
                "singleTitle": "查看详情",
                "singleURL": ""
            }
        }
    
    def render_multi_button_card(
        self, title: str, text: str, buttons: List[Dict[str, str]]
    ) -> RenderedMessage:
        """多按钮卡片"""
        return RenderedMessage(
            platform_type=self.platform_type,
            content={
                "msgtype": "actionCard",
                "actionCard": {
                    "title": title,
                    "text": text,
                    "btnOrientation": "1",
                    "btns": [
                        {"title": btn["title"], "actionURL": btn["url"]}
                        for btn in buttons
                    ]
                }
            },
            message_type="actionCard"
        )


class FeishuRenderer(BaseRenderer):
    """飞书渲染器 - 支持富文本卡片"""
    
    platform_type = PlatformType.FEISHU
    
    def render(self, msg: UnifiedMessage) -> RenderedMessage:
        content = self._render_card(msg.content)
        
        return RenderedMessage(
            platform_type=self.platform_type,
            content=content,
            message_type="interactive"
        )
    
    def _render_card(self, text: str) -> Dict[str, Any]:
        """渲染飞书富文本卡片"""
        lines = text.split("\n")
        elements = []
        
        for line in lines:
            if line.strip():
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": line
                    }
                })
        
        return {
            "msg_type": "interactive",
            "card": {
                "elements": elements,
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "客服消息"
                    }
                }
            }
        }


class SmsRenderer(BaseRenderer):
    """短信渲染器 - 纯文本，限制长度"""
    
    platform_type = PlatformType.SMS
    
    MAX_LENGTH = 500
    
    def render(self, msg: UnifiedMessage) -> RenderedMessage:
        text = self._render_text(msg.content)
        text = text[:self.MAX_LENGTH]
        
        return RenderedMessage(
            platform_type=self.platform_type,
            content=text,
            message_type="text"
        )
    
    def _render_text(self, text: str) -> str:
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        text = text.replace("\n", " ")
        return text


# 渲染器注册
_renderers: Dict[PlatformType, type] = {
    PlatformType.WEB: WebRenderer,
    PlatformType.WECHAT: WechatRenderer,
    PlatformType.WECHAT_MINIPROGRAM: WechatMiniprogramRenderer,
    PlatformType.DOUYIN: DouyinRenderer,
    PlatformType.DINGTALK: DingtalkRenderer,
    PlatformType.FEISHU: FeishuRenderer,
    PlatformType.SMS: SmsRenderer
}


def get_renderer(platform_type: PlatformType) -> BaseRenderer:
    """获取渲染器"""
    renderer_class = _renderers.get(platform_type)
    if not renderer_class:
        return BaseRenderer()
    return renderer_class()


def render_message(msg: UnifiedMessage) -> RenderedMessage:
    """根据平台类型渲染消息"""
    renderer = get_renderer(msg.platform_type)
    return renderer.render(msg)
