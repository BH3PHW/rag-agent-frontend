"""
知识库搜索工具
"""
from ..core.base import BaseTool, Parameter, ToolResult


class KBSearchTool(BaseTool):
    """知识库搜索工具"""
    
    name = "search_kb"
    description = "搜索知识库"
    tool_type = "DATA_QUERY"
    
    parameters = [
        Parameter(
            name="query",
            type="string",
            description="搜索查询内容",
            required=True
        )
    ]
    
    def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        
        if not query:
            return ToolResult(
                success=False,
                error="请提供搜索查询内容"
            )
        
        results = self.data_provider.search_knowledge_base(query)
        
        return ToolResult(
            success=True,
            data={
                "query": query,
                "count": len(results),
                "results": results
            }
        )
