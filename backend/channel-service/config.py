"""
渠道接入层 - 配置文件
"""
import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """渠道服务配置"""
    
    APP_NAME: str = "Channel Service"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8005
    
    DATABASE_URL: str = os.getenv("CHANNEL_DATABASE_URL", "postgresql://user:pass@db:5432/channel")
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    
    CHAT_SERVICE_URL: str = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8002")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    
    # 微信配置
    WECHAT_APPID: str = os.getenv("WECHAT_APPID", "")
    WECHAT_SECRET: str = os.getenv("WECHAT_SECRET", "")
    WECHAT_TOKEN: str = os.getenv("WECHAT_TOKEN", "")
    WECHAT_AES_KEY: str = os.getenv("WECHAT_AES_KEY", "")
    
    # 抖音配置
    DOUYIN_APP_KEY: str = os.getenv("DOUYIN_APP_KEY", "")
    DOUYIN_APP_SECRET: str = os.getenv("DOUYIN_APP_SECRET", "")
    
    # 钉钉配置
    DINGTALK_APP_KEY: str = os.getenv("DINGTALK_APP_KEY", "")
    DINGTALK_APP_SECRET: str = os.getenv("DINGTALK_APP_SECRET", "")
    
    # 飞书配置
    FEISHU_APP_ID: str = os.getenv("FEISHU_APP_ID", "")
    FEISHU_APP_SECRET: str = os.getenv("FEISHU_APP_SECRET", "")
    
    # 默认企业ID
    DEFAULT_ENTERPRISE_ID: str = "default-enterprise-id"
    
    class Config:
        env_file = ".env"


settings = Settings()
