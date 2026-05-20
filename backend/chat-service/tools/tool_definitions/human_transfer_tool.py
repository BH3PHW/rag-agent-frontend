"""
人工转介工具
"""
from ..core.base import BaseTool, Parameter, ToolResult


class HumanTransferTool(BaseTool):
    """人工转介工具"""
    
    name = "transfer_human"
    description = "转接人工客服"
    tool_type = "ACTION"
    
    parameters = [
        Parameter(
            name="reason",
            type="string",
            description="转介原因",
            required=False,
            default="用户请求人工服务"
        )
    ]
    
    def execute(self, **kwargs) -> ToolResult:
        reason = kwargs.get("reason", "用户请求人工服务")
        
        # 模拟转接处理
        transfer_id = f"TRF-{hash(reason) % 10000:04d}"
        
        return ToolResult(
            success=True,
            data={
                "transfer_id": transfer_id,
                "status": "in_progress",
                "message": "正在为您转接人工客服，请稍候..."
            },
            metadata={
                "reason": reason
            }
        )
