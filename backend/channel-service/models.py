"""
渠道接入层 - 数据模型
包含 OneID 映射、渠道配置、消息路由等模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, JSON, DateTime, Boolean, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class OneIDMapping(Base):
    """OneID 统一用户映射表
    
    将不同渠道的用户 ID 映射到统一的 unified_user_id
    """
    __tablename__ = "oneid_mappings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    unified_user_id = Column(String(128), nullable=False, index=True)
    
    platform_type = Column(String(32), nullable=False, index=True)
    platform_user_id = Column(String(128), nullable=False)
    
    phone = Column(String(32), nullable=True, index=True)
    unionid = Column(String(128), nullable=True, index=True)
    openid = Column(String(128), nullable=True)
    
    crm_user_id = Column(String(128), nullable=True, index=True)
    
    enterprise_id = Column(String(128), nullable=False)
    
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_platform_pair', 'platform_type', 'platform_user_id', 'enterprise_id'),
        Index('idx_phone', 'phone', 'enterprise_id'),
    )
    
    def __repr__(self):
        return f"<OneIDMapping {self.platform_type}:{self.platform_user_id} -> {self.unified_user_id}>"


class ChannelConfig(Base):
    """渠道配置表"""
    __tablename__ = "channel_configs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    enterprise_id = Column(String(128), nullable=False)
    channel_type = Column(String(32), nullable=False)
    
    app_id = Column(String(128), nullable=True)
    app_secret = Column(Text, nullable=True)
    token = Column(Text, nullable=True)
    aes_key = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    extra_config = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_enterprise_channel', 'enterprise_id', 'channel_type'),
    )


class MessageRoute(Base):
    """消息路由记录"""
    __tablename__ = "message_routes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    enterprise_id = Column(String(128), nullable=False)
    
    unified_user_id = Column(String(128), nullable=False)
    platform_type = Column(String(32), nullable=False)
    platform_user_id = Column(String(128), nullable=False)
    
    session_id = Column(String(128), nullable=True)
    
    original_platform_message_id = Column(String(256), nullable=True)
    
    direction = Column(String(16), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class PlatformSession(Base):
    """渠道会话表"""
    __tablename__ = "platform_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    enterprise_id = Column(String(128), nullable=False)
    
    platform_type = Column(String(32), nullable=False)
    platform_session_id = Column(String(128), nullable=False)
    
    unified_user_id = Column(String(128), nullable=False)
    
    chat_session_id = Column(String(128), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    last_message_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_platform_session', 'platform_type', 'platform_session_id', 'enterprise_id'),
    )


class EnterpriseChannelAccount(Base):
    """企业渠道账户表
    管理企业客户的所有渠道接入配置
    """
    __tablename__ = "enterprise_channel_accounts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    enterprise_id = Column(String(128), nullable=False, index=True)
    
    channel_name = Column(String(128), nullable=False, comment="渠道显示名称，如：微信公众号_客服")
    channel_type = Column(String(32), nullable=False, index=True, comment="渠道类型：web/wechat/wechat_miniprogram/douyin/dingtalk/feishu/sms/email")
    
    # 状态管理
    status = Column(String(32), nullable=False, default="draft", comment="状态：draft/active/inactive/error")
    is_active = Column(Boolean, default=True)
    
    # 配置信息
    app_id = Column(String(128), nullable=True)
    app_secret = Column(Text, nullable=True)
    token = Column(Text, nullable=True)
    aes_key = Column(Text, nullable=True)
    
    # 自定义配置
    extra_config = Column(JSON, nullable=True, comment="额外配置，如webhook URL、回调地址等")
    
    # webhook 配置
    webhook_url = Column(String(512), nullable=True, comment="平台回调地址（我们提供给外部的）")
    webhook_secret = Column(String(128), nullable=True, comment="webhook 签名密钥")
    
    # 统计信息
    message_count = Column(Integer, default=0, comment="消息总数")
    user_count = Column(Integer, default=0, comment="用户总数")
    last_message_at = Column(DateTime, nullable=True)
    
    # 备注
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_enterprise_channel_type', 'enterprise_id', 'channel_type'),
    )
    
    def __repr__(self):
        return f"<EnterpriseChannelAccount {self.channel_name}({self.channel_type})>"


class ChannelAccessLog(Base):
    """渠道接入日志表
    记录渠道的接入、消息、错误等日志
    """
    __tablename__ = "channel_access_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    enterprise_id = Column(String(128), nullable=False, index=True)
    channel_account_id = Column(String(36), nullable=True, index=True)
    channel_type = Column(String(32), nullable=False, index=True)
    
    log_type = Column(String(32), nullable=False, comment="日志类型：webhook/message/error/config")
    action = Column(String(128), nullable=True, comment="具体操作")
    
    request_data = Column(JSON, nullable=True, comment="请求数据")
    response_data = Column(JSON, nullable=True, comment="响应数据")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    status = Column(String(32), nullable=False, default="success", comment="状态：success/failed")
    duration_ms = Column(Integer, nullable=True, comment="处理耗时(ms)")
    
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

