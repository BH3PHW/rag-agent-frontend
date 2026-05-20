"""
内置工具定义（安全增强版）

功能：
1. 消费者身份识别 - 自动识别用户来自哪个电商平台
2. 订单查询 - 调用真实电商平台 API
3. 物流查询 - 获取实时物流信息
4. 商品查询 - 获取商品信息
5. 知识库和 FAQ
6. 安全验证 - 消费者身份验证、权限控制
"""
from typing import Dict, Any, Optional, List
import re
import sys
from pathlib import Path

try:
    from .tool_system import (
        ToolDefinition,
        ParameterDefinition,
        ToolType,
        get_tool_registry
    )
    from .security import SecurityContext, get_security_service
    from .ecommerce_integration import EcommerceIntegrationService
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from tool_system import (
        ToolDefinition,
        ParameterDefinition,
        ToolType,
        get_tool_registry
    )
    from security import SecurityContext, get_security_service
    from ecommerce_integration import EcommerceIntegrationService


# 全局安全上下文缓存（实际项目应该用更安全的方式）
_security_context_cache: Dict[str, SecurityContext] = {}


def set_current_security_context(context: SecurityContext, key: str = "default"):
    """设置当前安全上下文"""
    _security_context_cache[key] = context


def get_current_security_context(key: str = "default") -> Optional[SecurityContext]:
    """获取当前安全上下文"""
    return _security_context_cache.get(key)


def register_standard_tools() -> None:
    """注册标准工具"""
    registry = get_tool_registry()
    
    order_query = ToolDefinition(
        name="query_order",
        description="查询订单信息",
        tool_type=ToolType.DATA_QUERY,
        parameters=[
            ParameterDefinition(
                name="order_id",
                type="string",
                description="订单编号",
                required=True
            )
        ],
        handler=lambda **kwargs: order_query_tool(**kwargs)
    )
    
    product_info = ToolDefinition(
        name="query_product",
        description="查询商品信息",
        tool_type=ToolType.DATA_QUERY,
        parameters=[
            ParameterDefinition(
                name="product_name",
                type="string",
                description="商品名称",
                required=False
            ),
            ParameterDefinition(
                name="product_id",
                type="string",
                description="商品编号",
                required=False
            )
        ],
        handler=lambda **kwargs: product_info_tool(**kwargs)
    )
    
    kb_search = ToolDefinition(
        name="search_kb",
        description="搜索知识库",
        tool_type=ToolType.DATA_QUERY,
        parameters=[
            ParameterDefinition(
                name="query",
                type="string",
                description="搜索查询内容",
                required=True
            )
        ],
        handler=lambda **kwargs: kb_search_tool(**kwargs)
    )
    
    human_transfer = ToolDefinition(
        name="transfer_human",
        description="转接人工客服",
        tool_type=ToolType.BUSINESS_ACTION,
        parameters=[
            ParameterDefinition(
                name="reason",
                type="string",
                description="转介原因",
                required=False,
                default="用户请求人工服务"
            )
        ],
        handler=lambda **kwargs: human_transfer_tool(**kwargs)
    )
    
    faq_lookup = ToolDefinition(
        name="lookup_faq",
        description="查询常见问题",
        tool_type=ToolType.DATA_QUERY,
        parameters=[
            ParameterDefinition(
                name="question",
                type="string",
                description="用户的问题",
                required=True
            )
        ],
        handler=lambda **kwargs: faq_lookup_tool(**kwargs)
    )
    
    registry.register(order_query)
    registry.register(product_info)
    registry.register(kb_search)
    registry.register(human_transfer)
    registry.register(faq_lookup)


def register_ecommerce_tools() -> None:
    """注册电商工具 - 包含真实 API 调用"""
    registry = get_tool_registry()
    
    ecommerce_order = ToolDefinition(
        name="query_ecommerce_order",
        description="查询电商平台订单 - 支持多平台自动识别",
        tool_type=ToolType.DATA_QUERY,
        parameters=[
            ParameterDefinition(
                name="platform_type",
                type="string",
                description="电商平台(taobao/jd/douyin/pinduoduo/xianyu/xiaohongshu)",
                required=False
            ),
            ParameterDefinition(
                name="order_id",
                type="string",
                description="订单编号",
                required=False
            ),
            ParameterDefinition(
                name="user_message",
                type="string",
                description="用户原始消息（用于自动识别平台）",
                required=False
            )
        ],
        handler=lambda **kwargs: ecommerce_order_tool(**kwargs)
    )
    
    order_status = ToolDefinition(
        name="query_order_status",
        description="查询订单状态和物流信息",
        tool_type=ToolType.DATA_QUERY,
        parameters=[
            ParameterDefinition(
                name="platform_type",
                type="string",
                description="电商平台",
                required=True
            ),
            ParameterDefinition(
                name="order_id",
                type="string",
                description="订单编号",
                required=True
            )
        ],
        handler=lambda **kwargs: order_status_tool(**kwargs)
    )
    
    logistics_query = ToolDefinition(
        name="query_logistics",
        description="查询物流信息",
        tool_type=ToolType.DATA_QUERY,
        parameters=[
            ParameterDefinition(
                name="platform_type",
                type="string",
                description="电商平台",
                required=True
            ),
            ParameterDefinition(
                name="order_id",
                type="string",
                description="订单编号",
                required=True
            )
        ],
        handler=lambda **kwargs: logistics_query_tool(**kwargs)
    )
    
    ecommerce_product = ToolDefinition(
        name="query_ecommerce_product",
        description="查询电商平台商品",
        tool_type=ToolType.DATA_QUERY,
        parameters=[
            ParameterDefinition(
                name="platform_type",
                type="string",
                description="电商平台",
                required=False
            ),
            ParameterDefinition(
                name="product_name",
                type="string",
                description="商品名称",
                required=False
            ),
            ParameterDefinition(
                name="keyword",
                type="string",
                description="搜索关键词",
                required=False
            )
        ],
        handler=lambda **kwargs: ecommerce_product_tool(**kwargs)
    )
    
    ecommerce_platforms = ToolDefinition(
        name="list_ecommerce_platforms",
        description="获取电商平台列表",
        tool_type=ToolType.DATA_QUERY,
        parameters=[],
        handler=lambda **kwargs: ecommerce_platforms_tool(**kwargs)
    )
    
    consumer_identity = ToolDefinition(
        name="identify_consumer",
        description="识别消费者身份和来源平台",
        tool_type=ToolType.DATA_QUERY,
        parameters=[
            ParameterDefinition(
                name="user_message",
                type="string",
                description="用户消息",
                required=True
            ),
            ParameterDefinition(
                name="user_id",
                type="string",
                description="用户ID",
                required=False
            )
        ],
        handler=lambda **kwargs: consumer_identity_tool(**kwargs)
    )
    
    registry.register(ecommerce_order)
    registry.register(order_status)
    registry.register(logistics_query)
    registry.register(ecommerce_product)
    registry.register(ecommerce_platforms)
    registry.register(consumer_identity)


# ==================== 模拟数据（基础工具） ====================
MOCK_ORDERS = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "product_name": "智能蓝牙音箱",
        "customer_name": "张三",
        "customer_phone": "138****1234",
        "order_amount": 299,
        "order_status": "已发货",
        "created_at": "2024-01-15T10:30:00"
    }
}

MOCK_PRODUCTS = {
    "PROD-001": {
        "product_id": "PROD-001",
        "product_name": "智能蓝牙音箱",
        "price": 299,
        "stock": 100,
        "description": "高品质无线蓝牙音箱，支持语音控制"
    }
}

MOCK_KB = [
    {
        "id": "KB-001",
        "title": "退换货政策",
        "content": "我们支持7天无理由退换货，商品需保持原包装完好。",
        "category": "售后服务"
    }
]

MOCK_FAQS = {
    "退换货": {
        "question": "如何申请退换货？",
        "answer": "您可以在订单详情页点击申请退换货按钮，或联系客服处理。"
    }
}

ECOMMERCE_PLATFORMS = {
    "taobao": {"name": "淘宝/天猫", "enabled": True},
    "jd": {"name": "京东", "enabled": True},
    "douyin": {"name": "抖音商城", "enabled": True},
    "pinduoduo": {"name": "拼多多", "enabled": True},
    "xianyu": {"name": "闲鱼", "enabled": True},
    "xiaohongshu": {"name": "小红书", "enabled": True}
}


# ==================== 基础工具实现 ====================
def order_query_tool(
    order_id: str,
    enterprise_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """查询订单信息（带安全检查）"""
    security_context = get_current_security_context()
    
    if not security_context or not security_context.is_authenticated:
        return {
            "success": False,
            "error": "用户未认证，请先登录",
            "data": None
        }
    
    security_service = get_security_service()
    has_access, _ = security_service.verify_order_access(
        order_id=order_id,
        security_context=security_context
    )
    
    if not has_access:
        return {
            "success": False,
            "error": "没有权限访问该订单",
            "data": None
        }
    
    order = MOCK_ORDERS.get(order_id)
    if order:
        return {"success": True, "data": order}
    return {"success": False, "error": f"订单 {order_id} 未找到"}


def product_info_tool(
    product_name: str = None,
    product_id: Optional[str] = None,
    enterprise_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """查询商品信息"""
    if product_id:
        product = MOCK_PRODUCTS.get(product_id)
        if product:
            return {"success": True, "data": product}
    if product_name:
        products = [
            p for p in MOCK_PRODUCTS.values()
            if product_name.lower() in p["product_name"].lower()
        ]
        if products:
            return {"success": True, "data": products[0]}
    return {"success": False, "error": "未找到相关商品"}


def kb_search_tool(
    query: str,
    knowledge_base_id: Optional[str] = None,
    top_k: int = 5,
    enterprise_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """搜索知识库"""
    results = [
        kb for kb in MOCK_KB
        if query.lower() in kb["title"].lower() or query.lower() in kb["content"].lower()
    ]
    return {
        "success": True,
        "data": {
            "query": query,
            "count": len(results),
            "results": results
        }
    }


def human_transfer_tool(
    reason: str = "用户请求转接",
    priority: str = "normal",
    enterprise_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """人工转接工具"""
    return {
        "success": True,
        "data": {
            "transfer_id": f"TRF-{hash(reason) % 10000:04d}",
            "status": "in_progress",
            "message": "正在为您转接人工客服，请稍候..."
        }
    }


def faq_lookup_tool(
    question: str,
    category: Optional[str] = None,
    enterprise_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """FAQ查询工具"""
    for key, faq in MOCK_FAQS.items():
        if key in question:
            return {"success": True, "data": faq}
    return {
        "success": False,
        "error": "未找到相关的常见问题解答",
        "data": {"question": question}
    }


# ==================== 电商工具实现（安全增强版） ====================
def _analyze_platform_from_message(message: str) -> Optional[str]:
    """从用户消息中分析平台"""
    if not message:
        return None
    query_lower = message.lower()
    
    platform_keywords = {
        "taobao": ["淘宝", "taobao", "tb", "天猫", "ali"],
        "jd": ["京东", "jingdong", "jd"],
        "douyin": ["抖音", "douyin", "dy", "tiktok"],
        "pinduoduo": ["拼多多", "pinduoduo", "pdd"],
        "xianyu": ["闲鱼", "xianyu"],
        "xiaohongshu": ["小红书", "xiaohongshu", "xhs", "redbook"]
    }
    
    for platform, keywords in platform_keywords.items():
        if any(kw in query_lower for kw in keywords):
            return platform
    return None


def _extract_order_id_from_message(message: str) -> Optional[str]:
    """从用户消息中提取订单号"""
    if not message:
        return None
    patterns = [
        r'([A-Z]{2,}-\d+)',
        r'(taobao_\d+)',
        r'(jd_\d+)',
        r'(JD\d+)',
        r'(DY\d+)',
        r'(PDD\d+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def consumer_identity_tool(
    user_message: str,
    user_id: Optional[str] = None,
    enterprise_id: Optional[str] = None
) -> Dict[str, Any]:
    """消费者身份识别工具"""
    detected_platform = _analyze_platform_from_message(user_message)
    order_id = _extract_order_id_from_message(user_message)
    
    identity_info = {
        "detected": detected_platform is not None,
        "platform": detected_platform,
        "platform_name": ECOMMERCE_PLATFORMS.get(detected_platform, {}).get("name") if detected_platform else None,
        "order_id_found": order_id,
        "user_id": user_id,
        "enterprise_id": enterprise_id
    }
    
    if detected_platform:
        return {
            "success": True,
            "data": {
                "message": f"检测到您来自 {identity_info['platform_name']} 平台",
                "identity": identity_info,
                "can_query_orders": True,
                "can_query_logistics": True
            }
        }
    else:
        return {
            "success": True,
            "data": {
                "message": "无法自动识别您所在的平台，请告诉我您是在哪个平台购物的？",
                "identity": identity_info,
                "available_platforms": list(ECOMMERCE_PLATFORMS.keys())
            }
        }


def ecommerce_order_tool(
    platform_type: str = None,
    order_id: Optional[str] = None,
    user_message: Optional[str] = None,
    enterprise_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """电商订单查询工具（安全增强版）"""
    # 获取安全上下文
    security_context = get_current_security_context()
    
    if not security_context or not security_context.is_authenticated:
        return {
            "success": False,
            "error": "用户未认证，请先登录",
            "data": None
        }
    
    # 自动识别平台
    if not platform_type and user_message:
        platform_type = _analyze_platform_from_message(user_message)
    
    if not order_id and user_message:
        order_id = _extract_order_id_from_message(user_message)
    
    if not platform_type:
        return {
            "success": False,
            "error": "请指定平台类型",
            "hint": "支持的平台: taobao, jd, douyin, pinduoduo, xianyu, xiaohongshu"
        }
    
    if platform_type not in ECOMMERCE_PLATFORMS:
        return {
            "success": False,
            "error": f"不支持的平台: {platform_type}",
            "hint": "支持的平台: taobao, jd, douyin, pinduoduo, xianyu, xiaohongshu"
        }
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        EcommerceIntegrationService.get_platform_orders(
            platform_type=platform_type,
            enterprise_id=enterprise_id or security_context.enterprise_id or "default",
            order_id=order_id,
            security_context=security_context
        )
    )
    
    if result.get("success"):
        orders = result.get("orders", [])
        if orders:
            order = orders[0]
            return {
                "success": True,
                "data": {
                    "platform": platform_type,
                    "platform_name": ECOMMERCE_PLATFORMS[platform_type]["name"],
                    "order": order,
                    "formatted_message": _format_order_message(order)
                }
            }
        else:
            return {
                "success": False,
                "error": "未找到订单",
                "platform": platform_type
            }
    
    return result


def order_status_tool(
    platform_type: str,
    order_id: str,
    enterprise_id: Optional[str] = None
) -> Dict[str, Any]:
    """订单状态查询工具（安全增强版）"""
    security_context = get_current_security_context()
    
    if not security_context or not security_context.is_authenticated:
        return {
            "success": False,
            "error": "用户未认证"
        }
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            EcommerceIntegrationService.get_order_status(
                platform_type,
                order_id,
                enterprise_id or security_context.enterprise_id or "default",
                security_context
            )
        )
        return result
    except Exception:
        return {
            "success": False,
            "error": "查询订单状态失败"
        }


def logistics_query_tool(
    platform_type: str,
    order_id: str,
    enterprise_id: Optional[str] = None
) -> Dict[str, Any]:
    """物流查询工具（安全增强版）"""
    security_context = get_current_security_context()
    
    if not security_context or not security_context.is_authenticated:
        return {
            "success": False,
            "error": "用户未认证"
        }
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            EcommerceIntegrationService.get_logistics_info(
                platform_type,
                order_id,
                enterprise_id or security_context.enterprise_id or "default",
                security_context
            )
        )
        
        if result.get("success"):
            result["formatted_message"] = _format_logistics_message(result)
        
        return result
    except Exception:
        return {
            "success": False,
            "error": "查询物流信息失败"
        }


def ecommerce_product_tool(
    platform_type: str = None,
    product_name: Optional[str] = None,
    keyword: Optional[str] = None,
    enterprise_id: Optional[str] = None
) -> Dict[str, Any]:
    """电商商品查询"""
    mock_products = [
        {
            "product_id": f"{platform_type}_prod_001" if platform_type else "prod_001",
            "platform": platform_type or "general",
            "product_name": "热销商品示例",
            "price": 299,
            "stock": 100,
            "sales_count": 1250
        }
    ]
    return {
        "success": True,
        "data": {
            "platform": platform_type,
            "products": mock_products,
            "count": len(mock_products)
        }
    }


def ecommerce_platforms_tool(
    enterprise_id: Optional[str] = None
) -> Dict[str, Any]:
    """电商平台列表"""
    return {
        "success": True,
        "data": {
            "platforms": [
                {"id": pid, "name": p["name"], "enabled": p["enabled"]}
                for pid, p in ECOMMERCE_PLATFORMS.items()
            ]
        }
    }


# ==================== 辅助函数 ====================
def _format_order_message(order: Dict[str, Any]) -> str:
    """格式化订单消息"""
    lines = []
    lines.append(f"📦 订单信息")
    lines.append(f"平台：{order.get('platform', '未知')}")
    lines.append(f"订单号：{order.get('order_id', '未知')}")
    lines.append(f"商品：{order.get('product_name', '未知')}")
    lines.append(f"金额：¥{order.get('order_amount', 0)}")
    lines.append(f"状态：{order.get('order_status', '未知')}")
    
    if order.get("shipping_tracking_number"):
        lines.append(f"快递：{order.get('shipping_carrier', '未知')}")
        lines.append(f"单号：{order.get('shipping_tracking_number')}")
    
    return "\n".join(lines)


def _format_logistics_message(logistics: Dict[str, Any]) -> str:
    """格式化物流消息"""
    lines = []
    lines.append(f"🚚 物流信息")
    lines.append(f"快递：{logistics.get('carrier', '未知')}")
    lines.append(f"单号：{logistics.get('tracking_number', '未知')}")
    lines.append(f"状态：{logistics.get('status', '未知')}")
    
    timeline = logistics.get("timeline", [])
    if timeline:
        lines.append("\n📍 物流轨迹：")
        for item in timeline:
            lines.append(f"  {item['time']} - {item['status']} ({item['location']})")
    
    return "\n".join(lines)
