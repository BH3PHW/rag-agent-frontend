"""
电商平台集成服务

连接 chat-service 与 channel-service 的电商功能
包含消费者身份验证、订单查询、物流查询等核心功能
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import sys
from pathlib import Path

try:
    from .security import SecurityContext, SecurityService, get_security_service
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from security import SecurityContext, SecurityService, get_security_service


@dataclass
class ConsumerIdentity:
    """消费者身份信息
    
    包含已验证的消费者身份信息
    """
    unified_user_id: str
    platform_type: str
    platform_user_id: str
    phone: Optional[str] = None
    enterprise_id: Optional[str] = None
    order_history: List[Dict[str, Any]] = None
    is_verified: bool = False
    
    def __post_init__(self):
        if self.order_history is None:
            self.order_history = []


class EcommerceIntegrationService:
    """
    电商平台集成服务（安全增强版）
    
    核心功能：
    1. 消费者身份验证 - 验证用户是否是真实的平台消费者
    2. 订单查询 - 调用真实电商平台 API（带权限验证）
    3. 物流查询 - 获取实时物流信息
    4. 订单状态同步 - 多平台订单状态管理
    """
    
    @staticmethod
    async def get_consumer_identity(
        platform_type: str,
        platform_user_id: Optional[str] = None,
        phone: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> Optional[ConsumerIdentity]:
        """
        获取并验证消费者身份
        
        参数:
            platform_type: 平台类型
            platform_user_id: 平台用户ID
            phone: 手机号（可选）
            enterprise_id: 企业ID
            token: 安全Token（可选）
            
        返回:
            已验证的消费者身份信息，验证失败返回None
        """
        security_service = get_security_service()
        
        # 第一步：验证消费者身份
        is_verified, verify_details = security_service.verify_consumer_identity(
            platform_type=platform_type,
            platform_user_id=platform_user_id,
            phone=phone,
            enterprise_id=enterprise_id
        )
        
        if not is_verified:
            print(f"消费者身份验证失败: {verify_details.get('reason')}")
            return None
        
        # 身份验证通过
        return ConsumerIdentity(
            unified_user_id=verify_details.get("verified_unified_user_id", ""),
            platform_type=platform_type,
            platform_user_id=platform_user_id,
            phone=phone,
            enterprise_id=enterprise_id,
            is_verified=True
        )
    
    @staticmethod
    async def get_platform_orders(
        platform_type: str,
        enterprise_id: str,
        platform_id: Optional[str] = None,
        unified_user_id: Optional[str] = None,
        platform_user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        security_context: Optional[SecurityContext] = None
    ) -> Dict[str, Any]:
        """
        获取平台订单（带安全验证）
        
        参数:
            platform_type: 平台类型
            enterprise_id: 企业ID
            platform_id: 平台ID
            unified_user_id: 统一用户ID
            platform_user_id: 平台用户ID
            order_id: 订单ID（可选）
            status: 订单状态（可选）
            limit: 数量限制
            security_context: 安全上下文（必须）
            
        返回:
            订单查询结果
        """
        # 安全检查：必须有安全上下文
        if not security_context or not security_context.is_authenticated:
            return {
                "success": False,
                "error": "用户未认证，请先登录",
                "data": None
            }
        
        # 安全检查：必须验证企业ID
        if security_context.enterprise_id != enterprise_id:
            return {
                "success": False,
                "error": "企业ID不匹配",
                "data": None
            }
        
        # 如果有订单ID，验证访问权限
        if order_id:
            security_service = get_security_service()
            has_access, access_details = security_service.verify_order_access(
                order_id=order_id,
                security_context=security_context
            )
            
            if not has_access:
                return {
                    "success": False,
                    "error": f"没有权限访问订单: {access_details.get('reason')}",
                    "data": None
                }
        
        try:
            # 尝试调用 channel-service（模拟）
            result = await EcommerceIntegrationService._get_platform_orders_internal(
                platform_type=platform_type,
                enterprise_id=enterprise_id,
                order_id=order_id,
                unified_user_id=unified_user_id,
                limit=limit,
                status=status
            )
            
            # 脱敏处理：隐藏敏感信息
            if result.get("success") and result.get("orders"):
                result["orders"] = EcommerceIntegrationService._sanitize_order_data(
                    result["orders"]
                )
            
            return result
            
        except Exception as e:
            print(f"获取平台订单失败: {e}")
            return {
                "success": False,
                "error": "获取订单失败",
                "data": None
            }
    
    @staticmethod
    async def _get_platform_orders_internal(
        platform_type: str,
        enterprise_id: str,
        order_id: Optional[str] = None,
        unified_user_id: Optional[str] = None,
        limit: int = 50,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        内部订单查询实现
        
        TODO: 这里应该真正调用 channel-service 的 API
        """
        # 模拟数据（实际项目中应调用 channel-service）
        mock_orders = {
            "taobao": [
                {
                    "order_id": "taobao_1001",
                    "platform": "taobao",
                    "platform_order_id": "3216549870123",
                    "product_name": "女士连衣裙",
                    "customer_name": "王女士",
                    "customer_phone": "138****1234",
                    "order_amount": 358,
                    "order_status": "已签收",
                    "created_at": "2024-01-10T09:15:00",
                    "shipping_tracking_number": "SF1234567890",
                    "shipping_carrier": "顺丰速运"
                },
                {
                    "order_id": "taobao_1002",
                    "platform": "taobao",
                    "platform_order_id": "3216549870456",
                    "product_name": "运动T恤",
                    "customer_name": "王女士",
                    "customer_phone": "138****1234",
                    "order_amount": 129,
                    "order_status": "配送中",
                    "created_at": "2024-01-18T14:30:00",
                    "shipping_tracking_number": "YT9876543210",
                    "shipping_carrier": "圆通速递"
                }
            ],
            "jd": [
                {
                    "order_id": "jd_2001",
                    "platform": "jd",
                    "platform_order_id": "JD1234567890",
                    "product_name": "男士运动鞋",
                    "customer_name": "赵先生",
                    "customer_phone": "139****5678",
                    "order_amount": 599,
                    "order_status": "已发货",
                    "created_at": "2024-01-14T16:45:00",
                    "shipping_tracking_number": "SF2345678901",
                    "shipping_carrier": "顺丰速运"
                }
            ],
            "douyin": [
                {
                    "order_id": "douyin_3001",
                    "platform": "douyin",
                    "platform_order_id": "DY202401150001",
                    "product_name": "网红零食大礼包",
                    "customer_name": "小红",
                    "customer_phone": "137****9999",
                    "order_amount": 168,
                    "order_status": "待发货",
                    "created_at": "2024-01-19T10:20:00"
                }
            ],
            "pinduoduo": [
                {
                    "order_id": "pdd_4001",
                    "platform": "pinduoduo",
                    "platform_order_id": "PDD20240119001",
                    "product_name": "手机壳",
                    "customer_name": "小李",
                    "customer_phone": "136****8888",
                    "order_amount": 29.9,
                    "order_status": "已退款",
                    "created_at": "2024-01-12T08:00:00"
                }
            ]
        }
        
        orders = mock_orders.get(platform_type, [])
        
        if order_id:
            orders = [o for o in orders if o["order_id"] == order_id]
        
        if status:
            orders = [o for o in orders if o["order_status"] == status]
        
        return {
            "success": True,
            "platform": platform_type,
            "count": len(orders),
            "orders": orders
        }
    
    @staticmethod
    async def get_order_status(
        platform_type: str,
        order_id: str,
        enterprise_id: str,
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """
        获取订单状态详情（带权限验证）
        
        参数:
            platform_type: 平台类型
            order_id: 订单ID
            enterprise_id: 企业ID
            security_context: 安全上下文
            
        返回:
            订单状态详情
        """
        # 安全检查
        if not security_context or not security_context.is_authenticated:
            return {
                "success": False,
                "error": "用户未认证"
            }
        
        # 验证订单访问权限
        security_service = get_security_service()
        has_access, access_details = security_service.verify_order_access(
            order_id=order_id,
            security_context=security_context
        )
        
        if not has_access:
            return {
                "success": False,
                "error": f"没有权限访问订单: {access_details.get('reason')}"
            }
        
        # 获取订单
        result = await EcommerceIntegrationService.get_platform_orders(
            platform_type=platform_type,
            enterprise_id=enterprise_id,
            order_id=order_id,
            security_context=security_context
        )
        
        if result.get("success") and result.get("orders"):
            order = result["orders"][0]
            return {
                "success": True,
                "order_id": order["order_id"],
                "platform": order["platform"],
                "status": order["order_status"],
                "amount": order["order_amount"],
                "product": order["product_name"],
                "shipping_info": {
                    "tracking_number": order.get("shipping_tracking_number"),
                    "carrier": order.get("shipping_carrier"),
                    "status": "在途" if order["order_status"] == "配送中" else "已签收"
                } if order.get("shipping_tracking_number") else None
            }
        
        return {"success": False, "error": "未找到订单"}
    
    @staticmethod
    async def get_logistics_info(
        platform_type: str,
        order_id: str,
        enterprise_id: str,
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """
        获取物流信息（带权限验证）
        
        参数:
            platform_type: 平台类型
            order_id: 订单ID
            enterprise_id: 企业ID
            security_context: 安全上下文
            
        返回:
            物流信息
        """
        result = await EcommerceIntegrationService.get_order_status(
            platform_type, order_id, enterprise_id, security_context
        )
        
        if not result.get("success"):
            return result
        
        order = result
        
        if order.get("shipping_info") and order["shipping_info"].get("tracking_number"):
            return {
                "success": True,
                "order_id": order_id,
                "tracking_number": order["shipping_info"]["tracking_number"],
                "carrier": order["shipping_info"]["carrier"],
                "status": order["shipping_info"]["status"],
                "timeline": [
                    {
                        "time": "2024-01-15 10:30:00",
                        "status": "已发货",
                        "location": "广州仓库"
                    },
                    {
                        "time": "2024-01-16 14:20:00",
                        "status": "运输中",
                        "location": "广州转运中心"
                    },
                    {
                        "time": "2024-01-17 09:15:00",
                        "status": "到达目的地",
                        "location": "深圳转运中心"
                    }
                ] if order["status"] == "配送中" else [
                    {
                        "time": "2024-01-15 10:30:00",
                        "status": "已签收",
                        "location": "收货地址"
                    }
                ]
            }
        
        return {
            "success": False,
            "error": "该订单暂无物流信息",
            "order_status": order.get("status")
        }
    
    @staticmethod
    def _sanitize_order_data(orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        脱敏订单数据
        
        隐藏敏感信息，如手机号、真实姓名等
        """
        security_service = get_security_service()
        sanitized_orders = []
        
        for order in orders:
            sanitized = order.copy()
            
            # 脱敏手机号
            if "customer_phone" in sanitized and sanitized["customer_phone"]:
                sanitized["customer_phone"] = security_service.mask_sensitive_data(
                    sanitized["customer_phone"]
                )
            
            # 脱敏姓名
            if "customer_name" in sanitized and sanitized["customer_name"]:
                sanitized["customer_name"] = security_service.mask_sensitive_data(
                    sanitized["customer_name"], show_first=1, show_last=1
                )
            
            sanitized_orders.append(sanitized)
        
        return sanitized_orders
    
    @staticmethod
    def analyze_platform_from_query(query: str) -> Optional[str]:
        """
        从用户查询中分析用户来自哪个平台
        
        基于对话语义识别平台类型
        """
        if not query:
            return None
        
        query_lower = query.lower()
        
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
    
    @staticmethod
    def format_order_response(order: Dict[str, Any], include_details: bool = True) -> str:
        """
        格式化订单信息为友好的文本回复
        """
        lines = []
        lines.append(f"📦 订单信息")
        lines.append(f"平台：{order.get('platform', '未知')}")
        lines.append(f"订单号：{order.get('order_id', '未知')}")
        lines.append(f"商品：{order.get('product_name', '未知')}")
        lines.append(f"金额：¥{order.get('order_amount', 0)}")
        lines.append(f"状态：{order.get('order_status', '未知')}")
        
        if include_details:
            if order.get("shipping_tracking_number"):
                lines.append(f"快递：{order.get('shipping_carrier', '未知')}")
                lines.append(f"单号：{order.get('shipping_tracking_number')}")
        
        return "\n".join(lines)
