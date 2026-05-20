"""
工具注册表（已简化）
注：实际工具注册现在在 tool_system.py 中
此文件主要用于类型提示和向后兼容
"""
from typing import Dict, Any, Optional
from .base import BaseTool, ToolResult


# 保持向后兼容
class ToolRegistry:
    """工具注册表（简化版，主要用于类型提示）
    
    实际注册现在使用 tool_system.get_tool_registry()
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool):
        """注册工具（向后兼容）"""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> BaseTool:
        """获取工具（向后兼容）"""
        if name not in self._tools:
            raise ValueError(f"工具未找到: {name}")
        return self._tools[name]
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """获取所有工具（向后兼容）"""
        return dict(self._tools)
    
    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """执行工具（向后兼容）"""
        tool = self.get_tool(name)
        result = tool.execute(**kwargs)
        
        if isinstance(result, ToolResult):
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error
            }
        return result
    
    def clear(self):
        """清空所有工具（向后兼容）"""
        self._tools.clear()


# 全局注册表实例（向后兼容，实际使用 tool_system）
_registry_instance = None


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表（向后兼容）
    
    注意：新代码请使用 chat_service.tool_system.get_tool_registry()
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance
