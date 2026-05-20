"""
解耦工具系统（可选增强）

本模块提供更清晰的架构，但系统主要仍使用 built_in_tools.py 和 tool_system.py
以保持向后兼容性。

注意：主要工具系统位于 built_in_tools.py 和 tool_system.py 中
本目录中的内容为可选的增强架构，可用于未来的改进。
"""

# 导出核心内容，便于访问
from .core.base import BaseTool, Parameter, ToolResult, DataProvider
from .core.registry import ToolRegistry

__all__ = [
    "BaseTool",
    "Parameter",
    "ToolResult",
    "DataProvider",
    "ToolRegistry"
]
