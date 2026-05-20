"""
企业电商配置管理服务 - 完全配置化版本
支持动态添加平台和工具，无需重启服务
"""
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime
from .ecommerce_config_models import (
    EnterpriseEcommerceConfig,
    ToolConfig,
    PlatformRegistry,
    BUILTIN_PLATFORMS,
    BUILTIN_TOOLS
)
from .database import get_db


class EcommerceConfigService:
    """电商配置管理服务 - 完全配置化版本"""

    @staticmethod
    def _initialize_registry():
        """初始化平台注册表（仅首次使用）"""
        db = next(get_db())
        existing = db.query(PlatformRegistry).count()
        if existing == 0:
            for platform in BUILTIN_PLATFORMS:
                registry = PlatformRegistry(
                    id=str(uuid4()),
                    platform_id=platform["platform_id"],
                    name=platform["name"],
                    icon=platform["icon"],
                    api_type=platform["api_type"],
                    config_schema=platform["config_schema"]
                )
                db.add(registry)
            db.commit()

    @staticmethod
    async def get_all_platforms() -> List[Dict[str, Any]]:
        """获取所有已注册的平台（支持动态添加）"""
        EcommerceConfigService._initialize_registry()
        db = next(get_db())
        registries = db.query(PlatformRegistry).all()
        return [
            {
                "platform_id": r.platform_id,
                "name": r.name,
                "icon": r.icon,
                "api_type": r.api_type,
                "config_schema": r.config_schema,
                "enabled": r.enabled
            }
            for r in registries
        ]

    @staticmethod
    async def add_platform(
        platform_id: str,
        name: str,
        icon: str = "🔧",
        api_type: str = "custom",
        config_schema: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """添加新平台（无需重启服务）"""
        EcommerceConfigService._initialize_registry()
        db = next(get_db())
        
        existing = db.query(PlatformRegistry).filter(
            PlatformRegistry.platform_id == platform_id
        ).first()
        if existing:
            raise ValueError(f"平台 {platform_id} 已存在")
        
        registry = PlatformRegistry(
            id=str(uuid4()),
            platform_id=platform_id,
            name=name,
            icon=icon,
            api_type=api_type,
            config_schema=config_schema or {}
        )
        db.add(registry)
        db.commit()
        
        return {
            "platform_id": registry.platform_id,
            "name": registry.name,
            "icon": registry.icon
        }

    @staticmethod
    async def get_enterprise_platforms(enterprise_id: str) -> List[Dict[str, Any]]:
        """获取企业的电商平台配置（从注册表读取）"""
        EcommerceConfigService._initialize_registry()
        all_platforms = await EcommerceConfigService.get_all_platforms()
        
        db = next(get_db())
        configs = db.query(EnterpriseEcommerceConfig).filter(
            EnterpriseEcommerceConfig.enterprise_id == enterprise_id
        ).all()
        
        config_dict = {c.platform_id: c for c in configs}
        
        result = []
        for platform in all_platforms:
            config = config_dict.get(platform["platform_id"])
            result.append({
                "platform_id": platform["platform_id"],
                "name": platform["name"],
                "icon": platform["icon"],
                "api_type": platform["api_type"],
                "config_schema": platform["config_schema"],
                "enabled": config.enabled if config else platform["enabled"],
                "has_config": config is not None,
                "api_config": config.api_config if config else {},
                "sync_config": config.sync_config if config else {}
            })
        
        return result

    @staticmethod
    async def update_platform_config(
        enterprise_id: str,
        platform_id: str,
        enabled: bool,
        api_config: Optional[Dict] = None,
        sync_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """更新平台配置"""
        EcommerceConfigService._initialize_registry()
        db = next(get_db())
        
        # 验证平台ID是否存在
        registry = db.query(PlatformRegistry).filter(
            PlatformRegistry.platform_id == platform_id).first()
        if not registry:
            raise ValueError(f"不支持的平台: {platform_id}")
        
        # 更新或创建配置
        config = db.query(EnterpriseEcommerceConfig).filter(
            EnterpriseEcommerceConfig.enterprise_id == enterprise_id,
            EnterpriseEcommerceConfig.platform_id == platform_id
        ).first()
        
        if config:
            config.enabled = enabled
            if api_config:
                config.api_config = api_config
            if sync_config:
                config.sync_config = sync_config
            config.updated_at = datetime.utcnow()
        else:
            config = EnterpriseEcommerceConfig(
                id=str(uuid4()),
                enterprise_id=enterprise_id,
                platform_id=platform_id,
                platform_name=registry.name,
                enabled=enabled,
                api_config=api_config or {},
                sync_config=sync_config or {}
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        
        return {
            "platform_id": config.platform_id,
            "enabled": config.enabled,
            "api_config": config.api_config,
            "sync_config": config.sync_config,
            "updated_at": config.updated_at.isoformat()
        }

    @staticmethod
    async def get_tool_configs(enterprise_id: str) -> List[Dict[str, Any]]:
        """获取企业的工具配置（从内置配置）"""
        EcommerceConfigService._initialize_registry()
        db = next(get_db())
        
        # 获取企业已配置的工具
        configs = db.query(ToolConfig).filter(
            ToolConfig.enterprise_id == enterprise_id
        ).all()
        
        config_dict = {c.tool_name: c for c in configs}
        
        # 合并默认工具和企业配置
        result = []
        for tool_info in BUILTIN_TOOLS:
            config = config_dict.get(tool_info["tool_name"])
            result.append({
                "tool_name": tool_info["tool_name"],
                "name": tool_info["name"],
                "description": tool_info["description"],
                "category": tool_info["category"],
                "config_schema": tool_info["config_schema"],
                "enabled": config.enabled if config else True,
                "config": config.config if config else {}
            })
        
        return result

    @staticmethod
    async def update_tool_config(
        enterprise_id: str,
        tool_name: str,
        enabled: bool,
        config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """更新工具配置"""
        EcommerceConfigService._initialize_registry()
        db = next(get_db())
        
        # 验证工具名称是否在内置列表中
        tool_found = next((t for t in BUILTIN_TOOLS if t["tool_name"] == tool_name), None)
        if not tool_found:
            raise ValueError(f"不支持的工具: {tool_name}")
        
        # 更新配置
        tool_config = db.query(ToolConfig).filter(
            ToolConfig.enterprise_id == enterprise_id,
            ToolConfig.tool_name == tool_name
        ).first()
        
        if tool_config:
            tool_config.enabled = enabled
            if config:
                tool_config.config = config
            tool_config.updated_at = datetime.utcnow()
        else:
            tool_config = ToolConfig(
                id=str(uuid4()),
                enterprise_id=enterprise_id,
                tool_name=tool_name,
                enabled=enabled,
                config=config or {}
            )
            db.add(tool_config)
        
        db.commit()
        db.refresh(tool_config)
        
        return {
            "tool_name": tool_config.tool_name,
            "enabled": tool_config.enabled,
            "config": tool_config.config,
            "updated_at": tool_config.updated_at.isoformat()
        }

    @staticmethod
    async def get_enabled_platforms(enterprise_id: str) -> List[str]:
        """获取企业启用的平台列表"""
        platforms = await EcommerceConfigService.get_enterprise_platforms(enterprise_id)
        return [p["platform_id"] for p in platforms if p["enabled"]]

    @staticmethod
    async def get_enabled_tools(enterprise_id: str) -> List[str]:
        """获取企业启用的工具列表"""
        tools = await EcommerceConfigService.get_tool_configs(enterprise_id)
        return [t["tool_name"] for t in tools if t["enabled"]]
