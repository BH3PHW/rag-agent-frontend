"""
电商平台数据提供器 - 完全配置化版本
支持企业级配置和动态平台添加
"""
from typing import Dict, Any, Optional, List
from ..core.base import DataProvider
from ..ecommerce_config_service import EcommerceConfigService

# 默认电商订单示例（仅用于演示）
DEFAULT_ORDERS = {
    "taobao_1001": {
        "order_id": "taobao_1001",
        "platform": "taobao",
        "platform_order_id": "3216549870123",
        "product_name": "女士连衣裙",
        "customer_name": "王女士",
        "customer_phone": "136****8888",
        "order_amount": 358,
        "order_status": "已签收",
        "created_at": "2024-01-10T09:15:00"
    },
    "jd_2002": {
        "order_id": "jd_2002",
        "platform": "jd",
        "platform_order_id": "JD1234567890",
        "product_name": "男士运动鞋",
        "customer_name": "赵先生",
        "customer_phone": "137****9999",
        "order_amount": 599,
        "order_status": "配送中",
        "created_at": "2024-01-14T16:45:00"
    },
    "pdd_3003": {
        "order_id": "pdd_3003",
        "platform": "pdd",
        "platform_order_id": "PDD9876543210",
        "product_name": "儿童玩具车",
        "customer_name": "李女士",
        "customer_phone": "138****0000",
        "order_amount": 89,
        "order_status": "待发货",
        "created_at": "2024-01-15T10:30:00"
    },
    "douyin_4004": {
        "order_id": "douyin_4004",
        "platform": "douyin",
        "platform_order_id": "DY1122334455",
        "product_name": "化妆品套装",
        "customer_name": "张女士",
        "customer_phone": "139****1111",
        "order_amount": 299,
        "order_status": "已签收",
        "created_at": "2024-01-12T14:00:00"
    }
}

# 默认电商商品示例（仅用于演示）
DEFAULT_PRODUCTS = {
    "taobao_prod001": {
        "product_id": "taobao_prod001",
        "platform": "taobao",
        "product_name": "夏季雪纺连衣裙",
        "price": 258,
        "stock": 30,
        "sales_count": 1250,
        "platform_url": "https://item.taobao.com/item.htm?id=123456"
    },
    "jd_prod001": {
        "product_id": "jd_prod001",
        "platform": "jd",
        "product_name": "Nike Air Max运动鞋",
        "price": 899,
        "stock": 15,
        "sales_count": 680,
        "platform_url": "https://item.jd.com/12345678.html"
    },
    "pdd_prod001": {
        "product_id": "pdd_prod001",
        "platform": "pdd",
        "product_name": "家用收纳箱",
        "price": 45,
        "stock": 200,
        "sales_count": 5680,
        "platform_url": "https://mobile.pinduoduo.com/goods.html?goods_id=123456"
    }
}


class ConfigurableEcommerceDataProvider(DataProvider):
    """支持企业配置的电商平台数据提供器"""
    
    def __init__(self, enterprise_id: Optional[str] = None):
        self.enterprise_id = enterprise_id
        self.enabled_platforms = []
        self._load_config()
    
    def _load_config(self):
        """加载企业配置"""
        if self.enterprise_id:
            try:
                # 获取企业启用的平台（从配置服务获取）
                platforms = EcommerceConfigService.get_enabled_platforms(self.enterprise_id)
                self.enabled_platforms = platforms
            except Exception:
                # 如果获取配置失败，使用所有平台
                self.enabled_platforms = [
                    "taobao", "jd", "pdd", "douyin", "xianyu", "xiaohongshu"
                ]
        else:
            # 没有企业ID，使用所有平台
            self.enabled_platforms = [
                "taobao", "jd", "pdd", "douyin", "xianyu", "xiaohongshu"
            ]
    
    def _filter_by_platform(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根据企业配置过滤平台数据"""
        if not self.enterprise_id:
            return items
        return [item for item in items if item.get("platform") in self.enabled_platforms]
    
    def get_order(self, order_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """获取订单"""
        order = DEFAULT_ORDERS.get(order_id)
        if order and order.get("platform") in self.enabled_platforms:
            return order
        return None
    
    def get_product(self, product_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """获取商品"""
        product = DEFAULT_PRODUCTS.get(product_id)
        if product and product.get("platform") in self.enabled_platforms:
            return product
        return None
    
    def search_products(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """搜索商品"""
        results = []
        for p in DEFAULT_PRODUCTS.values():
            if p.get("platform") in self.enabled_platforms:
                if keyword.lower() in p["product_name"].lower():
                    results.append(p)
        return results
    
    def search_knowledge_base(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """搜索知识库"""
        return [
            {
                "id": "ECOM-001",
                "title": "多平台订单同步说明",
                "content": "系统支持多平台订单自动同步，平台可在企业配置中心管理。",
                "category": "平台操作"
            }
        ]
    
    def get_faqs(self, question: str, **kwargs) -> Optional[Dict[str, Any]]:
        """获取FAQ"""
        platform_names = ", ".join(self.enabled_platforms)
        
        faqs = {
            "平台": {
                "question": "支持哪些电商平台？",
                "answer": f"目前支持{platform_names}，更多平台可在企业配置中心添加。"
            },
            "同步": {
                "question": "订单多久同步一次？",
                "answer": "系统每30分钟自动同步各平台订单数据。"
            }
        }
        
        for key, faq in faqs.items():
            if key in question:
                return faq
        return None
    
    def get_platforms(self) -> List[Dict[str, Any]]:
        """获取所有电商平台配置（从配置服务获取）"""
        if self.enterprise_id:
            try:
                platforms = EcommerceConfigService.get_enterprise_platforms(self.enterprise_id)
                return [
                    {
                        "id": p["platform_id"],
                        "name": p["name"],
                        "enabled": p["enabled"]
                    }
                    for p in platforms
                ]
            except Exception:
                pass
        
        # 回退到默认平台列表
        default_platforms = {
            "taobao": {"name": "淘宝/天猫", "enabled": True},
            "jd": {"name": "京东", "enabled": True},
            "pdd": {"name": "拼多多", "enabled": True},
            "douyin": {"name": "抖音商城", "enabled": True},
            "xianyu": {"name": "闲鱼", "enabled": True},
            "xiaohongshu": {"name": "小红书", "enabled": True}
        }
        return [
            {"id": pid, "name": info["name"], "enabled": pid in self.enabled_platforms}
            for pid, info in default_platforms.items()
        ]
    
    def get_platform_orders(self, platform: str = None) -> List[Dict[str, Any]]:
        """获取指定平台的订单"""
        orders = list(DEFAULT_ORDERS.values())
        
        # 首先根据企业配置过滤
        orders = self._filter_by_platform(orders)
        
        # 然后根据平台参数过滤
        if platform:
            orders = [o for o in orders if o.get("platform") == platform]
        
        return orders
    
    def get_platform_products(self, platform: str = None) -> List[Dict[str, Any]]:
        """获取指定平台的商品"""
        products = list(DEFAULT_PRODUCTS.values())
        
        # 首先根据企业配置过滤
        products = self._filter_by_platform(products)
        
        # 然后根据平台参数过滤
        if platform:
            products = [p for p in products if p.get("platform") == platform]
        
        return products
