"""
工具系统基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Parameter:
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[list] = None


@dataclass
class ToolResult:
    """标准工具结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """工具抽象基类"""
    
    name: str = ""
    description: str = ""
    tool_type: str = "DATA_QUERY"
    parameters: list[Parameter] = field(default_factory=list)
    
    def __init__(self, data_provider=None):
        self.data_provider = data_provider
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """使用给定参数执行工具"""
        pass
    
    def get_definition(self) -> Dict[str, Any]:
        """获取工具定义用于注册"""
        return {
            "name": self.name,
            "description": self.description,
            "tool_type": self.tool_type,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "enum": p.enum
                }
                for p in self.parameters
            ]
        }


class DataProvider(ABC):
    """数据提供器抽象基类"""
    
    @abstractmethod
    def get_order(self, order_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """获取订单数据"""
        pass
    
    @abstractmethod
    def get_product(self, product_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def search_products(self, keyword: str, **kwargs) -> list:
        pass
    
    @abstractmethod
    def search_knowledge_base(self, query: str, **kwargs) -> list:
        pass
    
    @abstractmethod
    def get_faqs(self, question: str, **kwargs) -> Optional[Dict[str, Any]]:
        pass
