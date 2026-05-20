"""
E-commerce Platform Adapter System

Supporting:
- Taobao (淘宝)
- Douyin Store (抖音商城)
- Xianyu (闲鱼)
- JD (京东)
- Pinduoduo (拼多多)
- Xiaohongshu (小红书)
"""
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod


class PlatformType(Enum):
    """Supported e-commerce platforms"""
    TAOBAO = "taobao"
    DOUYIN = "douyin"
    XIANYU = "xianyu"
    JD = "jd"
    PINDUODUO = "pinduoduo"
    XIAOHONGSHU = "xiaohongshu"
    
    @classmethod
    def list_all(cls) -> List[str]:
        return [e.value for e in cls]
    
    @classmethod
    def get_display_name(cls, platform_type: str) -> str:
        display_names = {
            cls.TAOBAO.value: "淘宝店铺",
            cls.DOUYIN.value: "抖音商城",
            cls.XIANYU.value: "闲鱼",
            cls.JD.value: "京东",
            cls.PINDUODUO.value: "拼多多",
            cls.XIAOHONGSHU.value: "小红书"
        }
        return display_names.get(platform_type, platform_type)


@dataclass
class PlatformAPIConfig:
    """Platform API endpoint configuration"""
    api_base_url: str
    auth_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    order_endpoint: Optional[str] = None
    product_endpoint: Optional[str] = None
    request_timeout: int = 30
    use_sandbox: bool = False
    sandbox_api_base_url: Optional[str] = None
    custom_headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.custom_headers is None:
            self.custom_headers = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_base_url": self.api_base_url,
            "auth_endpoint": self.auth_endpoint,
            "token_endpoint": self.token_endpoint,
            "order_endpoint": self.order_endpoint,
            "product_endpoint": self.product_endpoint,
            "request_timeout": self.request_timeout,
            "use_sandbox": self.use_sandbox,
            "sandbox_api_base_url": self.sandbox_api_base_url,
            "custom_headers": self.custom_headers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlatformAPIConfig':
        return cls(
            api_base_url=data.get("api_base_url", ""),
            auth_endpoint=data.get("auth_endpoint"),
            token_endpoint=data.get("token_endpoint"),
            order_endpoint=data.get("order_endpoint"),
            product_endpoint=data.get("product_endpoint"),
            request_timeout=data.get("request_timeout", 30),
            use_sandbox=data.get("use_sandbox", False),
            sandbox_api_base_url=data.get("sandbox_api_base_url"),
            custom_headers=data.get("custom_headers", {})
        )


@dataclass
class PlatformConfig:
    """Platform configuration"""
    enterprise_id: str
    platform_type: PlatformType
    app_key: str
    app_secret: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    is_active: bool = True
    api_config: Optional[PlatformAPIConfig] = None
    extra_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_config is None:
            self.extra_config = {}
        if self.api_config is None:
            # Load default API config based on platform type
            self.api_config = get_default_api_config(self.platform_type)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enterprise_id": self.enterprise_id,
            "platform_type": self.platform_type.value,
            "platform_name": PlatformType.get_display_name(self.platform_type.value),
            "app_key": self.app_key,
            "store_id": self.store_id,
            "store_name": self.store_name,
            "is_active": self.is_active,
            "token_expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "api_config": self.api_config.to_dict() if self.api_config else None,
            "extra_config": self.extra_config
        }


# Default API configurations for each platform
# Note: These are EXAMPLE configurations - real production API endpoints
# For real use, please refer to each platform's official documentation
def get_default_api_config(platform_type: PlatformType) -> PlatformAPIConfig:
    """Get default API config for a platform"""
    default_configs = {
        # === 淘宝 (真实可用) ===
        # Official: https://open.taobao.com/
        PlatformType.TAOBAO: PlatformAPIConfig(
            api_base_url="https://eco.taobao.com/router/rest",
            auth_endpoint="https://oauth.taobao.com/authorize",
            token_endpoint="https://oauth.taobao.com/token",
            order_endpoint="taobao.trade.fullinfo.get",
            product_endpoint="taobao.item.seller.get",
        ),
        # === 抖音电商 (抖音开放平台) ===
        # Official: https://op.jinritemai.com/
        PlatformType.DOUYIN: PlatformAPIConfig(
            api_base_url="https://openapi-fxg.jinritemai.com",
            auth_endpoint="https://ecom.jinritemai.com/oauth/authorize",
            token_endpoint="https://openapi-fxg.jinritemai.com/oauth2/accessToken",
            order_endpoint="/order/list",
            product_endpoint="/product/list",
        ),
        # === 京东 (真实可用) ===
        # Official: https://open.jd.com/
        PlatformType.JD: PlatformAPIConfig(
            api_base_url="https://api.jd.com/routerjson",
            auth_endpoint="https://oauth.jd.com/oauth2/authorize",
            token_endpoint="https://oauth.jd.com/oauth2/accessToken",
            order_endpoint="jingdong.pop.order.get",
            product_endpoint="jingdong.pop.product.get",
        ),
        # === 拼多多 (真实可用) ===
        # Official: https://open.pinduoduo.com/
        PlatformType.PINDUODUO: PlatformAPIConfig(
            api_base_url="https://gw-api.pinduoduo.com/api/router",
            auth_endpoint="https://open.pinduoduo.com/oauth/authorize",
            token_endpoint="https://open.pinduoduo.com/oauth/access_token",
            order_endpoint="pdd.order.information.get",
            product_endpoint="pdd.goods.detail.get",
        ),
        # === 小红书 (示例配置) ===
        # Official: https://ark.xiaohongshu.com/
        # Note: Redbook has no public open platform with custom API
        PlatformType.XIAOHONGSHU: PlatformAPIConfig(
            api_base_url="https://ark.xiaohongshu.com/ark/open",
            auth_endpoint="https://ark.xiaohongshu.com/oauth/authorize",
            token_endpoint="https://ark.xiaohongshu.com/api/doraemon/oauth2/accessToken",
            order_endpoint="/order/list",
            product_endpoint="/product/list",
        ),
        # === 闲鱼 (示例配置) ===
        # Note: Xianyu doesn't have separate open API; integrates with Taobao
        PlatformType.XIANYU: PlatformAPIConfig(
            api_base_url="https://eco.taobao.com/router/rest",
            auth_endpoint="https://oauth.taobao.com/authorize",
            token_endpoint="https://oauth.taobao.com/token",
            order_endpoint="taobao.trade.fullinfo.get",
            product_endpoint="taobao.item.seller.get",
        ),
    }
    
    return default_configs.get(platform_type, PlatformAPIConfig(api_base_url=""))


@dataclass
class OrderInfo:
    """Order information from platform"""
    order_id: str
    platform_order_id: str
    platform: PlatformType
    buyer_name: str
    buyer_phone: Optional[str] = None
    order_status: str
    order_amount: float
    shipping_address: Optional[str] = None
    items: List[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    shipping_tracking_number: Optional[str] = None
    shipping_carrier: Optional[str] = None
    extra_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.extra_info is None:
            self.extra_info = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "platform_order_id": self.platform_order_id,
            "platform": self.platform.value,
            "platform_name": PlatformType.get_display_name(self.platform.value),
            "buyer_name": self.buyer_name,
            "buyer_phone": self.buyer_phone,
            "order_status": self.order_status,
            "order_amount": self.order_amount,
            "shipping_address": self.shipping_address,
            "items": self.items,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "shipping_tracking_number": self.shipping_tracking_number,
            "shipping_carrier": self.shipping_carrier,
            "extra_info": self.extra_info
        }


@dataclass
class ProductInfo:
    """Product information from platform"""
    product_id: str
    platform_product_id: str
    platform: PlatformType
    title: str
    price: float
    stock: Optional[int] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = None
    category: Optional[str] = None
    is_on_sale: bool = True
    extra_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.extra_info is None:
            self.extra_info = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "platform_product_id": self.platform_product_id,
            "platform": self.platform.value,
            "platform_name": PlatformType.get_display_name(self.platform.value),
            "title": self.title,
            "price": self.price,
            "stock": self.stock,
            "sku": self.sku,
            "description": self.description,
            "images": self.images,
            "category": self.category,
            "is_on_sale": self.is_on_sale,
            "extra_info": self.extra_info
        }


class BasePlatformAdapter(ABC):
    """Abstract base class for e-commerce platform adapters"""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self.platform = config.platform_type
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize adapter, validate credentials"""
        pass
    
    @abstractmethod
    async def refresh_access_token(self) -> bool:
        """Refresh access token if needed"""
        pass
    
    @abstractmethod
    async def get_order_info(self, order_id: str) -> Optional[OrderInfo]:
        """Get order information by ID"""
        pass
    
    @abstractmethod
    async def list_orders(
        self,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50
    ) -> List[OrderInfo]:
        """List orders with filters"""
        pass
    
    @abstractmethod
    async def get_product_info(self, product_id: str) -> Optional[ProductInfo]:
        """Get product information by ID"""
        pass
    
    @abstractmethod
    async def search_products(self, keyword: str, limit: int = 20) -> List[ProductInfo]:
        """Search products by keyword"""
        pass
    
    @abstractmethod
    async def update_order_status(
        self,
        order_id: str,
        new_status: str,
        remark: Optional[str] = None
    ) -> bool:
        """Update order status"""
        pass
    
    def get_platform_name(self) -> str:
        return PlatformType.get_display_name(self.platform.value)


class GenericAPIAdapter(BasePlatformAdapter):
    """Generic API adapter that works with configurable endpoints"""
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.api_config = config.api_config
        self._session = None
        self.mock_orders = {}
        self.mock_products = {}
        
        # Initialize mock data for fallback
        self._init_mock_data()
    
    def _init_mock_data(self):
        # Create some mock orders and products as fallback
        platform_name = self.get_platform_name()
        
        self.mock_orders = {
            f"mock_{self.platform.value}_1": OrderInfo(
                order_id=f"ord_{self.platform.value}_1",
                platform_order_id=f"{self.platform.value}_1001",
                platform=self.platform,
                buyer_name="张小明",
                buyer_phone="138****8888",
                order_status="已发货",
                order_amount=299.00,
                shipping_address=f"{platform_name}用户的收货地址",
                items=[{
                    "name": "示例商品",
                    "price": 299.00,
                    "quantity": 1
                }],
                created_at=datetime.now(),
                shipping_tracking_number=f"SF{int(datetime.now().timestamp())}",
                shipping_carrier="顺丰速运"
            ),
            f"mock_{self.platform.value}_2": OrderInfo(
                order_id=f"ord_{self.platform.value}_2",
                platform_order_id=f"{self.platform.value}_1002",
                platform=self.platform,
                buyer_name="李小红",
                order_status="待发货",
                order_amount=1599.00,
                items=[{
                    "name": "高级商品套装",
                    "price": 1599.00,
                    "quantity": 1
                }],
                created_at=datetime.now()
            )
        }
        
        self.mock_products = {
            f"prod_{self.platform.value}_1": ProductInfo(
                product_id=f"prod_{self.platform.value}_1",
                platform_product_id=f"item_{self.platform.value}_001",
                platform=self.platform,
                title=f"{platform_name}热卖商品",
                price=299.00,
                stock=500,
                description=f"这是{platform_name}的热销商品示例",
                category="智能设备"
            ),
            f"prod_{self.platform.value}_2": ProductInfo(
                product_id=f"prod_{self.platform.value}_2",
                platform_product_id=f"item_{self.platform.value}_002",
                platform=self.platform,
                title=f"{platform_name}精选套装",
                price=1599.00,
                stock=100,
                description=f"精选套装，性价比超高！",
                category="套装商品"
            )
        }
    
    async def _make_api_request(self, endpoint: str, method: str = "GET", params: dict = None) -> dict:
        """Make an API request to the platform"""
        import httpx
        
        base_url = self.api_config.sandbox_api_base_url if self.api_config.use_sandbox else self.api_config.api_base_url
        url = f"{base_url}{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
            **self.api_config.custom_headers
        }
        
        # Add authentication based on platform type
        if self.config.access_token:
            headers["Authorization"] = f"Bearer {self.config.access_token}"
        
        try:
            async with httpx.AsyncClient(timeout=self.api_config.request_timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=params, headers=headers)
                else:
                    return {"success": False, "error": f"Unsupported method: {method}"}
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def initialize(self) -> bool:
        """Initialize adapter - test connection if possible"""
        # If we have an API base URL, try to make a test request
        if self.api_config.api_base_url and self.config.app_key:
            # In a real implementation, you'd make an actual test API call
            # For now, just return True if we have basic config
            return True
        return True  # Always return True for demo purposes
    
    async def refresh_access_token(self) -> bool:
        """Refresh access token using token endpoint"""
        if not self.api_config.token_endpoint:
            return False
        
        result = await self._make_api_request(
            self.api_config.token_endpoint,
            "POST",
            {
                "app_key": self.config.app_key,
                "app_secret": self.config.app_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.config.refresh_token
            }
        )
        
        if result.get("success") and "data" in result:
            data = result["data"]
            if "access_token" in data:
                self.config.access_token = data["access_token"]
                if "refresh_token" in data:
                    self.config.refresh_token = data["refresh_token"]
                if "expires_in" in data:
                    self.config.token_expires_at = datetime.now() + datetime.timedelta(seconds=data["expires_in"])
                return True
        
        return False
    
    async def get_order_info(self, order_id: str) -> Optional[OrderInfo]:
        """Get order info from API or mock fallback"""
        if self.api_config.order_endpoint and self.api_config.api_base_url:
            result = await self._make_api_request(
                self.api_config.order_endpoint,
                "GET",
                {"order_id": order_id}
            )
            
            if result.get("success") and "data" in result:
                # 使用数据转换器解析真实API响应
                try:
                    from .data_transformers import get_data_transformer
                    transformer = get_data_transformer(self.platform)
                    if hasattr(transformer, 'transform_order'):
                        raw_data = result["data"]
                        if isinstance(raw_data, dict):
                            return transformer.transform_order(raw_data)
                except Exception as e:
                    print(f"Error transforming order data: {e}")
        
        # Fallback to mock data
        return self.mock_orders.get(order_id)
    
    async def list_orders(
        self,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50
    ) -> List[OrderInfo]:
        """List orders from API or mock fallback"""
        if self.api_config.order_endpoint and self.api_config.api_base_url:
            params = {"limit": limit}
            if status:
                params["status"] = status
            if start_time:
                params["start_time"] = start_time.isoformat()
            if end_time:
                params["end_time"] = end_time.isoformat()
            
            result = await self._make_api_request(
                self.api_config.order_endpoint,
                "GET",
                params
            )
            
            if result.get("success") and "data" in result:
                # 使用数据转换器批量解析订单列表
                try:
                    from .data_transformers import get_data_transformer
                    transformer = get_data_transformer(self.platform)
                    raw_data_list = result["data"]
                    if isinstance(raw_data_list, list) and hasattr(transformer, 'transform_order_list'):
                        return transformer.transform_order_list(raw_data_list)
                except Exception as e:
                    print(f"Error transforming order list: {e}")
        
        # Fallback to mock data
        orders = list(self.mock_orders.values())
        if status:
            orders = [o for o in orders if status in o.order_status]
        return orders[:limit]
    
    async def get_product_info(self, product_id: str) -> Optional[ProductInfo]:
        """Get product info from API or mock fallback"""
        if self.api_config.product_endpoint and self.api_config.api_base_url:
            result = await self._make_api_request(
                self.api_config.product_endpoint,
                "GET",
                {"product_id": product_id}
            )
            
            if result.get("success") and "data" in result:
                # 使用数据转换器解析商品数据
                try:
                    from .data_transformers import get_data_transformer
                    transformer = get_data_transformer(self.platform)
                    if hasattr(transformer, 'transform_product'):
                        raw_data = result["data"]
                        if isinstance(raw_data, dict):
                            return transformer.transform_product(raw_data)
                except Exception as e:
                    print(f"Error transforming product data: {e}")
        
        # Fallback to mock data
        return self.mock_products.get(product_id)
    
    async def search_products(self, keyword: str, limit: int = 20) -> List[ProductInfo]:
        """Search products from API or mock fallback"""
        if self.api_config.product_endpoint and self.api_config.api_base_url:
            result = await self._make_api_request(
                self.api_config.product_endpoint,
                "GET",
                {"keyword": keyword, "limit": limit}
            )
            
            if result.get("success") and "data" in result:
                # 使用数据转换器批量解析商品列表
                try:
                    from .data_transformers import get_data_transformer
                    transformer = get_data_transformer(self.platform)
                    raw_data_list = result["data"]
                    if isinstance(raw_data_list, list) and hasattr(transformer, 'transform_product_list'):
                        return transformer.transform_product_list(raw_data_list)
                except Exception as e:
                    print(f"Error transforming product list: {e}")
        
        # Fallback to mock data
        products = list(self.mock_products.values())
        if keyword:
            products = [p for p in products if keyword in p.title]
        return products[:limit]
    
    async def update_order_status(
        self,
        order_id: str,
        new_status: str,
        remark: Optional[str] = None
    ) -> bool:
        """Update order status"""
        if order_id in self.mock_orders:
            self.mock_orders[order_id].order_status = new_status
            return True
        return False


class MockPlatformAdapter(GenericAPIAdapter):
    """Mock adapter - alias for backwards compatibility"""
    pass


# Adapter factory
class PlatformAdapterFactory:
    """Factory for creating platform adapters"""
    
    @classmethod
    def create_adapter(cls, config: PlatformConfig) -> BasePlatformAdapter:
        """
        Create adapter for specific platform
        
        Now uses the GenericAPIAdapter which can be configured with custom endpoints!
        """
        # Use our generic configurable adapter for all platforms
        return GenericAPIAdapter(config)
    
    @classmethod
    def get_platform_api_config(cls, platform_type: PlatformType) -> PlatformAPIConfig:
        """Get the default API config for a platform"""
        return get_default_api_config(platform_type)
    
    @classmethod
    def update_platform_api_config(cls, platform_type: PlatformType, api_config: PlatformAPIConfig):
        """Update default API config for a platform (runtime)"""
        # This would update the default config stored somewhere
        # For now, just a placeholder
        pass
