"""
模拟数据提供器
提供模拟数据用于测试和开发
"""
from typing import Dict, Any, Optional, List
from ..core.base import DataProvider

# 模拟订单数据
MOCK_ORDERS = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "product_name": "智能蓝牙音箱",
        "customer_name": "张三",
        "customer_phone": "138****1234",
        "order_amount": 299,
        "order_status": "已发货",
        "created_at": "2024-01-15T10:30:00"
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "product_name": "无线耳机",
        "customer_name": "李四",
        "customer_phone": "139****5678",
        "order_amount": 199,
        "order_status": "待付款",
        "created_at": "2024-01-16T14:20:00"
    }
}

MOCK_PRODUCTS = {
    "PROD-001": {
        "product_id": "PROD-001",
        "product_name": "智能蓝牙音箱",
        "price": 299,
        "stock": 100,
        "description": "高品质无线蓝牙音箱，支持语音控制"
    },
    "PROD-002": {
        "product_id": "PROD-002",
        "product_name": "无线耳机",
        "price": 199,
        "stock": 250,
        "description": "降噪无线蓝牙耳机，续航40小时"
    },
    "PROD-003": {
        "product_id": "PROD-003",
        "product_name": "运动手环",
        "price": 159,
        "stock": 80,
        "description": "智能运动手环，支持心率监测"
    }
}

MOCK_KB_ENTRIES = [
    {
        "id": "KB-001",
        "title": "如何退换货政策",
        "content": "我们支持7天无理由退换货，商品需保持原包装完好。",
        "category": "售后服务"
    },
    {
        "id": "KB-002",
        "title": "配送时间说明",
        "content": "普通订单通常在24小时内发货，偏远地区3-5天送达。",
        "category": "配送服务"
    },
    {
        "id": "KB-003",
        "title": "保修政策",
        "content": "电子产品享受一年质保服务。",
        "category": "售后服务"
    }
]

MOCK_FAQS = {
    "退换货": {
        "question": "如何申请退换货？",
        "answer": "您可以在订单详情页点击申请退换货按钮，或联系客服处理。"
    },
    "物流": {
        "question": "订单发货后多久能到？",
        "answer": "一般1-3个工作日可送达，偏远地区可能需要3-5个工作日。"
    }
}


class MockDataProvider(DataProvider):
    """模拟数据提供器"""
    
    def get_order(self, order_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        return MOCK_ORDERS.get(order_id)
    
    def get_product(self, product_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        return MOCK_PRODUCTS.get(product_id)
    
    def search_products(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        return [
            p for p in MOCK_PRODUCTS.values()
            if keyword.lower() in p["product_name"].lower()
        ]
    
    def search_knowledge_base(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        return [
            entry for entry in MOCK_KB_ENTRIES
            if query.lower() in entry["title"].lower() or
               query.lower() in entry["content"].lower()
        ]
    
    def get_faqs(self, question: str, **kwargs) -> Optional[Dict[str, Any]]:
        for key, faq in MOCK_FAQS.items():
            if key in question:
                return faq
        return None
