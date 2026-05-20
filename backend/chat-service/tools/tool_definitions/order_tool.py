"""
订单查询工具
"""
from typing import Dict, Any
from ..core.base import BaseTool, Parameter, ToolResult


class OrderQueryTool(BaseTool):
    """订单查询工具"""
    
    name = "query_order"
    description = "查询订单信息"
    tool_type = "DATA_QUERY"
    
    parameters = [
        Parameter(
            name="order_id",
            type="string",
            description="订单编号",
            required=True
        )
    ]
    
    def execute(self, **kwargs) -> ToolResult:
        order_id = kwargs.get("order_id")
        
        if not order_id:
            return ToolResult(
                success=False,
                error="请提供订单编号"
            )
        
        order = self.data_provider.get_order(order_id)
        
        if order:
            return ToolResult(
                success=True,
                data=order
            )
        else:
            return ToolResult(
                success=False,
                error=f"订单 {order_id} 未找到"
            )
