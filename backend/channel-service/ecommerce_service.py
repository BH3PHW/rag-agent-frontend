"""
E-commerce Platform Management Service
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from .models import EcommercePlatformConfig, generate_uuid
from .ecommerce_platforms import (
    PlatformType, PlatformConfig, PlatformAPIConfig, PlatformAdapterFactory,
    OrderInfo, ProductInfo, get_default_api_config
)


class EcommercePlatformService:
    """电商平台管理服务"""
    
    @staticmethod
    def list_platforms(
        db: Session,
        enterprise_id: str,
        is_active: Optional[bool] = None
    ) -> List[EcommercePlatformConfig]:
        """列出企业配置的所有平台"""
        query = db.query(EcommercePlatformConfig).filter(
            EcommercePlatformConfig.enterprise_id == enterprise_id
        )
        
        if is_active is not None:
            query = query.filter(EcommercePlatformConfig.is_active == is_active)
        
        return query.order_by(EcommercePlatformConfig.created_at.desc()).all()
    
    @staticmethod
    def get_platform(
        db: Session,
        platform_id: str,
        enterprise_id: str
    ) -> Optional[EcommercePlatformConfig]:
        """获取特定平台配置"""
        return db.query(EcommercePlatformConfig).filter(
            EcommercePlatformConfig.id == platform_id,
            EcommercePlatformConfig.enterprise_id == enterprise_id
        ).first()
    
    @staticmethod
    def create_platform(
        db: Session,
        enterprise_id: str,
        platform_type: str,
        platform_name: str,
        app_key: str,
        app_secret: str,
        store_id: Optional[str] = None,
        store_name: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        sync_orders: bool = True,
        sync_products: bool = True,
        auto_reply: bool = True,
        description: Optional[str] = None,
        extra_config: Optional[Dict[str, Any]] = None
    ) -> EcommercePlatformConfig:
        """创建平台配置"""
        platform_config = EcommercePlatformConfig(
            id=generate_uuid(),
            enterprise_id=enterprise_id,
            platform_type=platform_type,
            platform_name=platform_name,
            app_key=app_key,
            app_secret=app_secret,
            store_id=store_id,
            store_name=store_name,
            access_token=access_token,
            refresh_token=refresh_token,
            sync_orders=sync_orders,
            sync_products=sync_products,
            auto_reply=auto_reply,
            description=description,
            extra_config=extra_config,
            status="draft"
        )
        
        db.add(platform_config)
        db.commit()
        db.refresh(platform_config)
        
        return platform_config
    
    @staticmethod
    def update_platform(
        db: Session,
        platform_id: str,
        enterprise_id: str,
        **kwargs
    ) -> Optional[EcommercePlatformConfig]:
        """更新平台配置"""
        platform = EcommercePlatformService.get_platform(db, platform_id, enterprise_id)
        if not platform:
            return None
        
        allowed_fields = [
            "platform_name", "app_key", "app_secret", 
            "access_token", "refresh_token",
            "store_id", "store_name",
            "sync_orders", "sync_products", "auto_reply",
            "is_active", "status", "description", "extra_config"
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(platform, field):
                setattr(platform, field, value)
        
        platform.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(platform)
        
        return platform
    
    @staticmethod
    def delete_platform(
        db: Session,
        platform_id: str,
        enterprise_id: str
    ) -> bool:
        """删除平台配置"""
        platform = EcommercePlatformService.get_platform(db, platform_id, enterprise_id)
        if not platform:
            return False
        
        db.delete(platform)
        db.commit()
        return True
    
    @staticmethod
    def get_available_platforms() -> List[Dict[str, Any]]:
        """获取所有支持的电商平台列表"""
        return [
            {
                "type": PlatformType.TAOBAO.value,
                "name": PlatformType.get_display_name(PlatformType.TAOBAO.value),
                "description": "淘宝店铺接入",
                "fields": ["app_key", "app_secret", "access_token"]
            },
            {
                "type": PlatformType.DOUYIN.value,
                "name": PlatformType.get_display_name(PlatformType.DOUYIN.value),
                "description": "抖音商城接入",
                "fields": ["app_key", "app_secret", "access_token", "store_id"]
            },
            {
                "type": PlatformType.XIANYU.value,
                "name": PlatformType.get_display_name(PlatformType.XIANYU.value),
                "description": "闲鱼接入",
                "fields": ["app_key", "app_secret"]
            },
            {
                "type": PlatformType.JD.value,
                "name": PlatformType.get_display_name(PlatformType.JD.value),
                "description": "京东店铺接入",
                "fields": ["app_key", "app_secret", "access_token"]
            },
            {
                "type": PlatformType.PINDUODUO.value,
                "name": PlatformType.get_display_name(PlatformType.PINDUODUO.value),
                "description": "拼多多接入",
                "fields": ["app_key", "app_secret", "access_token"]
            },
            {
                "type": PlatformType.XIAOHONGSHU.value,
                "name": PlatformType.get_display_name(PlatformType.XIAOHONGSHU.value),
                "description": "小红书店铺接入",
                "fields": ["app_key", "app_secret", "access_token"]
            }
        ]
    
    @staticmethod
    async def test_platform_connection(
        db: Session,
        platform_id: str,
        enterprise_id: str
    ) -> Dict[str, Any]:
        """测试平台连接"""
        platform = EcommercePlatformService.get_platform(db, platform_id, enterprise_id)
        if not platform:
            return {"success": False, "error": "平台配置不存在"}
        
        try:
            # Parse API config from extra_config if available
            api_config = None
            if platform.extra_config and "api_config" in platform.extra_config:
                api_config = PlatformAPIConfig.from_dict(platform.extra_config["api_config"])
            
            config = PlatformConfig(
                enterprise_id=enterprise_id,
                platform_type=PlatformType(platform.platform_type),
                app_key=platform.app_key or "",
                app_secret=platform.app_secret or "",
                access_token=platform.access_token,
                store_id=platform.store_id,
                api_config=api_config
            )
            
            adapter = PlatformAdapterFactory.create_adapter(config)
            connected = await adapter.initialize()
            
            if connected:
                platform.status = "active"
                platform.last_sync_at = datetime.utcnow()
                db.commit()
                
                return {"success": True, "message": "连接成功"}
            else:
                platform.status = "error"
                db.commit()
                
                return {"success": False, "error": "连接测试失败"}
                
        except Exception as e:
            platform.status = "error"
            db.commit()
            
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_platform_orders(
        db: Session,
        platform_id: str,
        enterprise_id: str,
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """获取平台订单"""
        platform = EcommercePlatformService.get_platform(db, platform_id, enterprise_id)
        if not platform or not platform.is_active:
            return {"success": False, "error": "平台配置不存在或未启用"}
        
        try:
            # Parse API config from extra_config if available
            api_config = None
            if platform.extra_config and "api_config" in platform.extra_config:
                api_config = PlatformAPIConfig.from_dict(platform.extra_config["api_config"])
            
            config = PlatformConfig(
                enterprise_id=enterprise_id,
                platform_type=PlatformType(platform.platform_type),
                app_key=platform.app_key or "",
                app_secret=platform.app_secret or "",
                access_token=platform.access_token,
                store_id=platform.store_id,
                api_config=api_config
            )
            
            adapter = PlatformAdapterFactory.create_adapter(config)
            
            if order_id:
                order = await adapter.get_order_info(order_id)
                if order:
                    return {"success": True, "orders": [order.to_dict()]}
                else:
                    return {"success": True, "orders": []}
            else:
                orders = await adapter.list_orders(status=status, limit=limit)
                return {"success": True, "orders": [o.to_dict() for o in orders]}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_platform_products(
        db: Session,
        platform_id: str,
        enterprise_id: str,
        product_id: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取平台商品"""
        platform = EcommercePlatformService.get_platform(db, platform_id, enterprise_id)
        if not platform or not platform.is_active:
            return {"success": False, "error": "平台配置不存在或未启用"}
        
        try:
            # Parse API config from extra_config if available
            api_config = None
            if platform.extra_config and "api_config" in platform.extra_config:
                api_config = PlatformAPIConfig.from_dict(platform.extra_config["api_config"])
            
            config = PlatformConfig(
                enterprise_id=enterprise_id,
                platform_type=PlatformType(platform.platform_type),
                app_key=platform.app_key or "",
                app_secret=platform.app_secret or "",
                access_token=platform.access_token,
                store_id=platform.store_id,
                api_config=api_config
            )
            
            adapter = PlatformAdapterFactory.create_adapter(config)
            
            if product_id:
                product = await adapter.get_product_info(product_id)
                if product:
                    return {"success": True, "products": [product.to_dict()]}
                else:
                    return {"success": True, "products": []}
            elif keyword:
                products = await adapter.search_products(keyword, limit=limit)
                return {"success": True, "products": [p.to_dict() for p in products]}
            else:
                return {"success": True, "products": []}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_platform_api_config(
        db: Session,
        platform_id: str,
        enterprise_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取平台 API 配置"""
        platform = EcommercePlatformService.get_platform(db, platform_id, enterprise_id)
        if not platform:
            return None
        
        # Get API config from extra_config or return default
        if platform.extra_config and "api_config" in platform.extra_config:
            return platform.extra_config["api_config"]
        
        # Return default config for the platform
        default_config = get_default_api_config(PlatformType(platform.platform_type))
        return default_config.to_dict()
    
    @staticmethod
    def update_platform_api_config(
        db: Session,
        platform_id: str,
        enterprise_id: str,
        api_config_dict: Dict[str, Any]
    ) -> Optional[EcommercePlatformConfig]:
        """更新平台 API 配置"""
        platform = EcommercePlatformService.get_platform(db, platform_id, enterprise_id)
        if not platform:
            return None
        
        # Update extra_config with API config
        if platform.extra_config is None:
            platform.extra_config = {}
        
        platform.extra_config["api_config"] = api_config_dict
        platform.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(platform)
        
        return platform
    
    @staticmethod
    def reset_platform_api_config(
        db: Session,
        platform_id: str,
        enterprise_id: str
    ) -> Optional[EcommercePlatformConfig]:
        """重置平台 API 配置为默认值"""
        platform = EcommercePlatformService.get_platform(db, platform_id, enterprise_id)
        if not platform:
            return None
        
        # Get default config
        default_config = get_default_api_config(PlatformType(platform.platform_type))
        
        # Update extra_config
        if platform.extra_config is None:
            platform.extra_config = {}
        
        platform.extra_config["api_config"] = default_config.to_dict()
        platform.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(platform)
        
        return platform
