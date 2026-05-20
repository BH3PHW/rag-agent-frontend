"""
工具加载器
负责自动发现和加载工具定义
"""
import importlib
import pkgutil
import sys
from pathlib import Path
from typing import List, Type

# 先导入核心模块，避免相对导入问题
from .base import BaseTool


def discover_tools(module_path: str, package_path: Path) -> List[Type[BaseTool]]:
    """从模块路径发现所有工具类"""
    tools = []
    
    # 确保模块路径在sys.path中
    parent_path = str(package_path.parent)
    if parent_path not in sys.path:
        sys.path.insert(0, parent_path)
    
    # 遍历包中的所有模块
    for _, modname, _ in pkgutil.iter_modules([str(package_path)]):
        if modname.startswith('_'):
            continue
            
        try:
            # 导入模块
            full_module_path = f"{module_path}.{modname}"
            module = importlib.import_module(full_module_path)
            
            # 查找BaseTool的子类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseTool) and 
                    attr is not BaseTool and
                    hasattr(attr, 'name') and 
                    attr.name):
                    tools.append(attr)
                    
        except Exception as e:
            print(f"警告：加载模块 {modname} 时出错: {e}")
    
    return tools


def load_tools(data_provider=None) -> int:
    """加载并注册所有工具到 tool_system 注册表"""
    # 延迟导入避免循环导入
    try:
        from ..data_providers.mock_provider import MockDataProvider
        from ...tool_system import (
            get_tool_registry,
            ToolDefinition,
            ParameterDefinition,
            ToolType
        )
    except ImportError as e:
        print(f"警告：模块导入问题: {e}")
        return 0
    
    # 使用默认的模拟数据提供器
    if data_provider is None:
        data_provider = MockDataProvider()
    
    registry = get_tool_registry()
    
    # 获取当前文件的路径
    current_dir = Path(__file__).parent.parent
    
    # 发现工具定义
    tool_classes = []
    try:
        # 尝试从当前包结构发现工具
        tool_classes = discover_tools(
            module_path="chat-service.tools.tool_definitions",
            package_path=current_dir / "tool_definitions"
        )
    except Exception:
        pass
    
    if not tool_classes:
        try:
            tool_classes = discover_tools(
                module_path="tools.tool_definitions",
                package_path=current_dir / "tool_definitions"
            )
        except Exception as e:
            print(f"工具发现失败: {e}")
    
    # 辅助函数：转换参数
    def _convert_params(params):
        return [
            ParameterDefinition(
                name=p.name,
                type=p.type,
                description=p.description,
                required=p.required,
                default=p.default,
                enum=p.enum
            ) for p in params
        ]
    
    # 辅助函数：创建工具包装器
    def _create_wrapper(tool_instance):
        def wrapper(**kwargs):
            accepted_params = [p.name for p in tool_instance.parameters]
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in accepted_params}
            result = tool_instance.execute(**filtered_kwargs)
            if hasattr(result, '__dict__'):
                return getattr(result, 'data', result)
            return result
        return wrapper
    
    # 注册工具到 tool_system 注册表
    count = 0
    for tool_cls in tool_classes:
        try:
            tool_instance = tool_cls(data_provider)
            
            # 处理工具类型
            tool_type_enum = ToolType.DATA_QUERY
            if hasattr(tool_cls, 'tool_type'):
                try:
                    tool_type_enum = ToolType(tool_cls.tool_type)
                except ValueError:
                    pass
            
            # 创建工具定义
            tool_def = ToolDefinition(
                name=tool_cls.name,
                description=tool_cls.description,
                tool_type=tool_type_enum,
                parameters=_convert_params(tool_cls.parameters),
                handler=_create_wrapper(tool_instance),
                requires_auth=True,
                enterprise_scoped=True
            )
            
            registry.register(tool_def)
            count += 1
        except Exception as e:
            print(f"警告：注册工具 {tool_cls} 失败: {e}")
    
    return count
