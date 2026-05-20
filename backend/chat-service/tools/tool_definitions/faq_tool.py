"""
常见问题解答工具
"""
from ..core.base import BaseTool, Parameter, ToolResult


class FAQTool(BaseTool):
    """常见问题解答工具"""
    
    name = "lookup_faq"
    description = "获取常见问题解答"
    tool_type = "DATA_QUERY"
    
    parameters = [
        Parameter(
            name="question",
            type="string",
            description="用户的问题",
            required=True
        )
    ]
    
    def execute(self, **kwargs) -> ToolResult:
        question = kwargs.get("question", "")
        
        if not question:
            return ToolResult(
                success=False,
                error="请提供问题"
            )
        
        faq = self.data_provider.get_faqs(question)
        
        if faq:
            return ToolResult(
                success=True,
                data=faq
            )
        else:
            return ToolResult(
                success=False,
                error="未找到相关的常见问题解答",
                data={"question": question}
            )
