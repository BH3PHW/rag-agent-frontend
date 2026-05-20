"""
企业电商工具配置模型 - 完全配置化版本
"""
from sqlalchemy import Column, String, JSON, Boolean, DateTime
from datetime import datetime
from .database import Base

class PlatformRegistry(Base):
    """平台注册表 - 支持动态添加新平台"""
    __tablename__ = "platform_registry"
    
    id = Column(String, primary_key=True, index=True)
    platform_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    icon = Column(String, default="🔧")
    api_type = Column(String)  # 平台类型: taobao_api, jd_api 等
    config_schema = Column(JSON)  # 配置项定义
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EnterpriseEcommerceConfig(Base):
    """企业电商配置"""
    __tablename__ = "enterprise_ecommerce_config"

    id = Column(String, primary_key=True, index=True)
    enterprise_id = Column(String, index=True, nullable=False)
    platform_id = Column(String, index=True, nullable=False)
    platform_name = Column(String)
    enabled = Column(Boolean, default=True)
    api_config = Column(JSON)  # API密钥等配置
    sync_config = Column(JSON)  # 同步配置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ToolConfig(Base):
    """工具配置"""
    __tablename__ = "tool_config"

    id = Column(String, primary_key=True, index=True)
    enterprise_id = Column(String, index=True, nullable=False)
    tool_name = Column(String, index=True, nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(JSON)  # 工具特定配置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 内置默认平台（仅用于初始化）
BUILTIN_PLATFORMS = [
    {
        "platform_id": "taobao",
        "name": "淘宝/天猫",
        "icon": "🛒",
        "api_type": "taobao_api",
        "config_schema": {
            "app_key": {"type": "string", "label": "App Key"},
            "app_secret": {"type": "string", "label": "App Secret"}
        }
    },
    {
        "platform_id": "jd",
        "name": "京东",
        "icon": "📦",
        "api_type": "jd_api",
        "config_schema": {
            "app_key": {"type": "string", "label": "App Key"},
            "app_secret": {"type": "string", "label": "App Secret"}
        }
    },
    {
        "platform_id": "pdd",
        "name": "拼多多",
        "icon": "💰",
        "api_type": "pdd_api",
        "config_schema": {
            "client_id": {"type": "string", "label": "Client ID"},
            "client_secret": {"type": "string", "label": "Client Secret"}
        }
    },
    {
        "platform_id": "douyin",
        "name": "抖音商城",
        "icon": "🎵",
        "api_type": "douyin_api",
        "config_schema": {
            "app_key": {"type": "string", "label": "App Key"},
            "app_secret": {"type": "string", "label": "App Secret"}
        }
    },
    {
        "platform_id": "xianyu",
        "name": "闲鱼",
        "icon": "♻️",
        "api_type": "xianyu_api",
        "config_schema": {
            "api_key": {"type": "string", "label": "API Key"}
        }
    },
    {
        "platform_id": "xiaohongshu",
        "name": "小红书",
        "icon": "📕",
        "api_type": "xiaohongshu_api",
        "config_schema": {
            "app_id": {"type": "string", "label": "App ID"},
            "app_secret": {"type": "string", "label": "App Secret"}
        }
    }
]

# 内置默认工具配置（仅用于初始化）
BUILTIN_TOOLS = [
    {
        "tool_name": "query_ecommerce_order",
        "name": "订单查询",
        "description": "查询电商平台订单信息",
        "category": "order",
        "config_schema": {
            "max_results": {"type": "number", "label": "最大查询数量", "default": 50}
        }
    },
    {
        "tool_name": "query_ecommerce_product",
        "name": "商品查询",
        "description": "查询电商平台商品信息",
        "category": "product",
        "config_schema": {}
    },
    {
        "tool_name": "search_ecommerce_products",
        "name": "商品搜索",
        "description": "搜索电商平台商品",
        "category": "product",
        "config_schema": {
            "default_platform": {"type": "string", "label": "默认查询平台"}
        }
    }
]
