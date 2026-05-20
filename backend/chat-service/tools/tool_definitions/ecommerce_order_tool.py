"""
电商订单查询工具
"""
from ..core.base import BaseTool, Parameter, ToolResult


class EcommerceOrderTool(BaseTool):
    """电商订单查询工具"""
    
    name = "query_ecommerce_order"
    description = "查询电商平台订单"
    tool_type = "DATA_QUERY"
    
    parameters = [
        Parameter(
            name="platform_type",
            type="string",
            description="电商平台(taobao/jd/pdd/douyin/xianyu/xiaohongshu)",
            required=False
        ),
        Parameter(
            name="platform",
            type="string",
            description="电商平台(可选，同platform_type)",
            required=False
        ),
        Parameter(
            name="order_id",
            type="string",
            description="订单编号(可选)",
            required=False
        )
    ]
    
    def execute(self, **kwargs) -> ToolResult:
        platform = kwargs.get("platform_type") or kwargs.get("platform")
        order_id = kwargs.get("order_id")
        
        # 检查是否有额外的平台查询方法
        if hasattr(self.data_provider, 'get_platform_orders'):
            if order_id:
                # 先尝试直接通过ID获取
                order = self.data_provider.get_order(order_id)
                if order:
                    return ToolResult(
                        success=True,
                        data=order
                    )
            
            # 获取平台订单列表
            orders = self.data_provider.get_platform_orders(platform)
            return ToolResult(
                success=True,
                data={
                    "platform": platform or "all",
                    "count": len(orders),
                    "orders": orders
                }
            )
        
        # 回退到基础查询
        if order_id:
            order = self.data_provider.get_order(order_id)
            if order:
                return ToolResult(success=True, data=order)
            return ToolResult(success=False, error=f"订单 {order_id} 未找到")
        
        return ToolResult(
            success=False,
            error="请提供订单编号或平台"
        )
