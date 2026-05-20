"""
Agent Core with Function Calling Integration
增强版：支持电商平台自动识别和消费者身份识别
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import json
import re

from .tool_system import (
    get_tool_registry,
    get_tool_executor,
    ToolExecutionResult,
    ToolDefinition
)
from .built_in_tools import register_standard_tools, register_ecommerce_tools


class AgentDecision:
    """Agent decision about whether to use tools"""

    def __init__(
        self,
        use_tools: bool,
        tools_to_call: List[Dict[str, Any]] = None,
        reasoning: str = ""
    ):
        self.use_tools = use_tools
        self.tools_to_call = tools_to_call or []
        self.reasoning = reasoning


class AgentExecutor:
    """
    Agent executor that manages function calling workflow
    
    增强功能：
    1. 电商平台自动识别
    2. 消费者身份识别
    3. 智能工具选择
    4. 订单状态和物流查询
    """

    def __init__(self):
        self.registry = get_tool_registry()
        self.executor = get_tool_executor()

        # 注册标准工具和电商工具
        register_standard_tools()
        register_ecommerce_tools()

    async def analyze_and_execute(
        self,
        query: str,
        conversation_history: List[Dict[str, Any]] = None,
        enterprise_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[bool, List[ToolExecutionResult], str]:
        """
        分析查询并执行必要的工具
        """
        tools_used, tools_to_call = self._rule_based_tool_selection(query)

        if not tools_used:
            return False, [], "No tools needed for this query"

        results = []
        for tool_call in tools_to_call:
            tool_name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})

            result = await self.executor.execute(
                tool_name=tool_name,
                arguments=arguments,
                enterprise_id=enterprise_id,
                user_id=user_id
            )

            results.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result
            })

        return True, results, f"Used {len(results)} tools"

    def _rule_based_tool_selection(self, query: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        增强版基于规则的工具选择
        
        智能路由：
        1. 优先识别电商相关查询
        2. 自动识别消费者来源平台
        3. 根据查询类型选择最合适的工具
        """
        query_lower = query.lower()
        tools_to_call = []

        # 平台检测映射（扩展关键词）
        platform_keywords = {
            "taobao": ["淘宝", "taobao", "tb", "天猫", "ali"],
            "jd": ["京东", "jingdong", "jd"],
            "douyin": ["抖音", "douyin", "dy", "tiktok"],
            "pinduoduo": ["拼多多", "pinduoduo", "pdd"],
            "xianyu": ["闲鱼", "xianyu"],
            "xiaohongshu": ["小红书", "xiaohongshu", "xhs", "redbook"]
        }

        # 检测是否为电商相关查询
        is_ecommerce_query = any(
            any(kw in query_lower for kw in keywords)
            for keywords in platform_keywords.values()
        )

        # 检测查询类型
        is_order_query = any(keyword in query_lower for keyword in ["订单", "发货", "ord-", "买了", "购买"])
        is_logistics_query = any(keyword in query_lower for keyword in ["物流", "快递", "到哪了", "什么时候到", "发货了"])
        is_product_query = any(keyword in query_lower for keyword in ["产品", "商品", "价格", "库存", "规格", "多少钱", "有货吗"])
        is_platform_list_query = any(keyword in query_lower for keyword in ["平台", "店铺", "已对接", "有哪些平台"])
        
        # 提取订单号
        order_match = re.search(r'([A-Z]{2,}-\d+|taobao_\d+|jd_\d+|JD\d+|DY\d+|PDD\d+)', query, re.IGNORECASE)
        extracted_order_id = order_match.group(1) if order_match else None

        # 电商查询优先处理
        if is_ecommerce_query:
            # 识别平台类型
            detected_platform = None
            for platform, keywords in platform_keywords.items():
                if any(kw in query_lower for kw in keywords):
                    detected_platform = platform
                    break

            if detected_platform:
                # 物流查询优先
                if is_logistics_query:
                    if extracted_order_id:
                        tools_to_call.append({
                            "name": "query_logistics",
                            "arguments": {
                                "platform_type": detected_platform,
                                "order_id": extracted_order_id
                            }
                        })
                    elif is_order_query:
                        # 查询订单状态（包含物流信息）
                        tools_to_call.append({
                            "name": "query_order_status",
                            "arguments": {
                                "platform_type": detected_platform,
                                "order_id": extracted_order_id or "taobao_1001"  # 默认订单
                            }
                        })
                    else:
                        # 只知道平台，先列出订单
                        tools_to_call.append({
                            "name": "query_ecommerce_order",
                            "arguments": {
                                "platform_type": detected_platform,
                                "user_message": query
                            }
                        })
                # 订单查询
                elif is_order_query:
                    tools_to_call.append({
                        "name": "query_ecommerce_order",
                        "arguments": {
                            "platform_type": detected_platform,
                            "order_id": extracted_order_id,
                            "user_message": query
                        }
                    })
                # 电商商品查询
                elif is_product_query:
                    tools_to_call.append({
                        "name": "query_ecommerce_product",
                        "arguments": {
                            "platform_type": detected_platform,
                            "product_name": query
                        }
                    })
                # 仅平台关键词，先列出平台和订单
                else:
                    tools_to_call.append({
                        "name": "query_ecommerce_order",
                        "arguments": {
                            "platform_type": detected_platform,
                            "user_message": query
                        }
                    })
            # 平台列表查询
            elif is_platform_list_query:
                tools_to_call.append({
                    "name": "list_ecommerce_platforms",
                    "arguments": {}
                })
        # 传统订单查询（非电商平台）
        elif is_order_query:
            if extracted_order_id:
                tools_to_call.append({
                    "name": "query_order",
                    "arguments": {
                        "order_id": extracted_order_id
                    }
                })
            else:
                tools_to_call.append({
                    "name": "query_order",
                    "arguments": {
                        "order_id": "ORD-1001"
                    }
                })
        # 传统商品查询
        elif is_product_query:
            tools_to_call.append({
                "name": "query_product",
                "arguments": {
                    "product_name": query
                }
            })
        # FAQ查找
        elif any(keyword in query_lower for keyword in ["如何", "怎么", "什么是", "FAQ", "常见问题"]):
            tools_to_call.append({
                "name": "lookup_faq",
                "arguments": {
                    "question": query
                }
            })
        # 人工转接
        elif any(keyword in query_lower for keyword in ["人工", "客服", "转人工"]):
            tools_to_call.append({
                "name": "transfer_human",
                "arguments": {
                    "reason": "用户请求人工客服",
                    "priority": "normal"
                }
            })
        # 知识库搜索（兜底）
        elif len(query) > 3:
            tools_to_call.append({
                "name": "search_kb",
                "arguments": {
                    "query": query
                }
            })

        return len(tools_to_call) > 0, tools_to_call

    def format_tool_results_for_llm(self, tool_results: List[Dict[str, Any]]) -> str:
        """
        格式化工具执行结果以供 LLM 使用
        """
        if not tool_results:
            return ""

        sections = []
        sections.append("===== 工具调用结果 =====")

        for i, result in enumerate(tool_results, 1):
            tool_name = result.get("tool_name")
            execution_result = result.get("result")

            sections.append(f"\n【工具 {i}: {tool_name}】")

            if execution_result.success:
                sections.append("状态: ✅ 成功")
                if execution_result.data:
                    data_str = json.dumps(execution_result.data, ensure_ascii=False, indent=2)
                    sections.append(f"数据:\n{data_str}")
            else:
                sections.append(f"状态: ❌ 失败")
                sections.append(f"错误: {execution_result.error_message}")

            sections.append(f"执行耗时: {execution_result.execution_time_ms:.2f}ms")

        sections.append("\n===== 请根据以上工具调用结果回答用户问题 =====")

        return "\n".join(sections)

    def get_available_tools_description(self) -> str:
        """
        获取所有可用工具的描述以供 LLM 提示词使用
        """
        tools = self.registry.list_tools()

        lines = ["===== 可用工具列表 ====="]

        for tool in tools:
            lines.append(f"\n【{tool.name}】")
            lines.append(f"类型: {tool.tool_type.value}")
            lines.append(f"描述: {tool.description}")

            param_lines = []
            for param in tool.parameters:
                req = " [必填]" if param.required else " [可选]"
                param_lines.append(f"  - {param.name} ({param.type}){req}: {param.description}")

            if param_lines:
                lines.append("参数:")
                lines.extend(param_lines)

        lines.append("\n=====================")

        return "\n".join(lines)


# Singleton instance
_agent_executor: Optional[AgentExecutor] = None


def get_agent_executor() -> AgentExecutor:
    """Get singleton AgentExecutor"""
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = AgentExecutor()
    return _agent_executor
