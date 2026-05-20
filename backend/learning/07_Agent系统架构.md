# 第7章：Agent系统架构

> 🎯 **学习目标**：理解Agent如何分析问题、决定调用工具、执行动作

---

## 7.1 什么是Agent？

### 核心概念

**Agent = 能感知环境 → 做出决策 → 执行动作的智能体**

在客服场景：
```
用户问题 → Agent分析 → 判断需要什么工具 → 调用工具 → 整合结果 → 回答用户
```

### 传统RAG vs Agent RAG

| 特性 | 传统RAG | Agent RAG |
|------|---------|-----------|
| **能力** | 仅检索知识库 | 可调用各种工具 |
| **问题** | "退换货政策"没问题 | "查我的订单状态"不行 |
| **灵活度** | 固定流程 | 动态决策 |

---

## 7.2 Agent工作流程

### 完整流程图

```
用户问题
    ↓
[1. 理解] 分析问题意图
    ↓
[2. 决策] 是否需要调用工具？
    ↓ 否
[直接回答] 用RAG回答
    ↓ 是
[3. 选择] 选择合适的工具
    ↓
[4. 执行] 调用工具获取数据
    ↓
[5. 整合] 把工具结果作为上下文
    ↓
[6. 生成] LLM生成最终回答
```

### 关键代码（来自 [agent_system.py](../../chat-service/agent_system.py)）

```python
class AgentExecutor:
    """
    Agent执行器，管理工具调用流程
    
    主要步骤：
    1. analyze_and_execute() - 分析并执行
    2. _rule_based_tool_selection() - 规则选择工具
    3. executor.execute() - 执行工具
    """
    
    async def analyze_and_execute(
        self,
        query: str,
        conversation_history: List[Dict[str, Any]] = None,
        enterprise_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[bool, List[ToolExecutionResult], str]:
        """分析查询并执行必要的工具"""
        
        # 步骤1：规则选择工具
        tools_used, tools_to_call = self._rule_based_tool_selection(query)
        
        if not tools_used:
            return False, [], "No tools needed for this query"
        
        # 步骤2：执行工具
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
                "result": result
            })
        
        return True, results, "Tools executed successfully"
```

---

## 7.3 工具系统架构

### 工具注册机制

项目采用**注册模式**，让工具添加更灵活：

```
工具定义 (ToolDefinition)
    ↓
工具注册表 (ToolRegistry)
    ↓
工具执行器 (ToolExecutor)
    ↓
Agent调用
```

### 目录结构

```
chat-service/tools/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── base.py          ← 工具基类
│   ├── registry.py      ← 注册表
│   └── loader.py        ← 加载器
├── data_providers/
│   ├── __init__.py
│   ├── mock_provider.py ← 模拟数据
│   └── ecommerce_provider.py ← 电商数据
└── tool_definitions/
    ├── __init__.py
    ├── order_tool.py       ← 订单查询
    ├── product_tool.py     ← 商品查询
    ├── kb_search_tool.py   ← 知识库搜索
    ├── faq_tool.py         ← FAQ查询
    ├── human_transfer_tool.py  ← 人工转接
    ├── ecommerce_order_tool.py   ← 电商订单
    └── ecommerce_product_tool.py ← 电商商品
```

---

## 7.4 内置工具详解

### 标准工具（5个）

| 工具名称 | 功能 | 适用场景 |
|---------|------|---------|
| `query_order` | 订单查询 | "我的订单到哪了？" |
| `query_product` | 商品查询 | "这款手机多少钱？" |
| `search_kb` | 知识库搜索 | "产品说明书在哪里？" |
| `lookup_faq` | FAQ查询 | "运费谁承担？" |
| `transfer_human` | 人工转接 | "我要找客服" |

### 电商工具（3个新增）

| 工具名称 | 功能 |
|---------|------|
| `query_ecommerce_order` | 多平台订单查询 |
| `query_ecommerce_product` | 多平台商品查询 |
| `list_ecommerce_platforms` | 可用平台列表 |

---

## 7.5 工具定义规范

### 工具基类（[tools/core/base.py](../../chat-service/tools/core/base.py)）

```python
class BaseTool:
    """工具基类"""
    
    name: str  # 工具名称
    description: str  # 描述
    parameters: Dict[str, Any]  # 参数定义
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """执行工具"""
        raise NotImplementedError()
```

### 具体工具示例（订单查询）

看 [tools/tool_definitions/order_tool.py](../../chat-service/tools/tool_definitions/order_tool.py)：

```python
class OrderQueryTool(BaseTool):
    name = "query_order"
    description = "查询订单状态和物流信息"
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "订单号"
            }
        },
        "required": ["order_id"]
    }
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        order_id = arguments["order_id"]
        # 查询订单...
        return {
            "order_id": order_id,
            "status": "shipping",
            "tracking_number": "SF1234567890"
        }
```

---

## 7.6 工具选择策略

### 规则匹配（当前实现）

项目使用**基于规则**的工具选择，更快速可靠：

```python
def _rule_based_tool_selection(self, query: str) -> Tuple[bool, List[Dict]]:
    """
    基于规则选择工具
    
    规则示例：
    - 包含"订单"、"物流" → query_order
    - 包含"商品"、"价格" → query_product
    - 包含"人工"、"客服" → transfer_human
    """
    
    tools_to_call = []
    
    # 规则1：订单查询
    if any(keyword in query for keyword in ["订单", "物流", "发货"]):
        # 尝试提取订单号
        order_id = self._extract_order_id(query)
        if order_id:
            tools_to_call.append({
                "name": "query_order",
                "arguments": {"order_id": order_id}
            })
    
    # 规则2：商品查询
    if any(keyword in query for keyword in ["商品", "价格", "多少钱"]):
        product_name = self._extract_product_name(query)
        if product_name:
            tools_to_call.append({
                "name": "query_product",
                "arguments": {"product_name": product_name}
            })
    
    return len(tools_to_call) > 0, tools_to_call
```

### 未来可扩展：LLM决策

更智能的方式：让LLM判断用什么工具

```python
# 伪代码示例
async def _llm_tool_selection(self, query: str):
    """让LLM选择工具"""
    
    prompt = f"""
用户问题：{query}

可用工具：
- query_order: 查订单
- query_product: 查商品
- search_kb: 搜知识库

应该用哪个工具？返回JSON格式：
{{"use_tool": true/false, "tool_name": "...", "arguments": {{...}}}}
"""
    
    llm_response = await call_llm(prompt)
    return parse_tool_call(llm_response)
```

---

## 7.7 完整对话示例

### 场景：用户查订单

```
用户：我的订单SF123456到哪了？
    ↓
Agent分析：
    意图：查订单
    关键词：订单、SF123456
    工具：query_order
    ↓
调用工具：query_order(order_id="SF123456")
    ↓
工具返回：
{
    "status": "派送中",
    "tracking_info": "今天上午9点已到达配送站"
}
    ↓
Agent整合：LLM根据工具结果生成回答
    ↓
回答：您的订单SF123456正在派送中，今天上午9点已到达配送站...
```

---

## 7.8 数据提供层

### 为什么需要数据提供层？

```
工具定义 ← 数据提供层 ← 实际数据源
           (mock或真实)
```

好处：
- ✅ 工具逻辑与数据源解耦
- ✅ 可以用mock数据测试
- ✅ 可以切换不同的数据源

### 示例：电商数据提供

看 [tools/data_providers/ecommerce_provider.py](../../chat-service/tools/data_providers/ecommerce_provider.py)：

```python
class EcommerceDataProvider:
    """电商数据提供器"""
    
    async def get_order(self, platform: str, order_id: str):
        """从指定平台获取订单"""
        
        if platform == "taobao":
            return await self._call_taobao_api(order_id)
        elif platform == "jd":
            return await self._call_jd_api(order_id)
        # ...
```

---

## 7.10 工程化与产品化思维在本章的体现

### 🛠️ 工程化思维

Agent系统的工程化设计体现在以下几个方面：

| 工程化要素 | 在Agent中的体现 |
|-----------|------------|
| **模块化设计** | 工具基类、注册表、执行器各自独立 |
| **可扩展性** | 新增工具只需注册，无需修改核心代码 |
| **依赖注入** | 数据提供器通过构造函数注入 |
| **类型安全** | 使用枚举定义工具类型、参数类型 |
| **错误处理** | 统一返回ToolExecutionResult结构 |
| **可测试性** | MockDataProvider支持无依赖测试 |

**关键工程化决策**：

```python
# 1. 插件化架构 - 新增工具只需注册
def register_ecommerce_tools():
    registry = get_tool_registry()
    
    # 新增工具只需定义并注册
    ecommerce_order = ToolDefinition(
        name="query_ecommerce_order",
        description="查询电商平台订单",
        handler=lambda **kwargs: ecommerce_order_tool(**kwargs)
    )
    registry.register(ecommerce_order)

# 2. 数据与逻辑分离 - DataProvider模式
class OrderTool(BaseTool):
    def __init__(self, data_provider=None):
        self.data_provider = data_provider or MockDataProvider()
    
    def execute(self, **kwargs):
        # 工具逻辑与数据源解耦
        return self.data_provider.get_order(kwargs["order_id"])

# 3. 统一的结果格式
@dataclass
class ToolExecutionResult:
    success: bool
    data: Any = None
    error_message: str = None
    execution_time_ms: float = 0
```

### 🎯 产品化思维

Agent系统的产品化设计体现在以下几个方面：

| 产品化要素 | 在Agent中的体现 |
|-----------|------------|
| **用户体验** | 智能识别用户意图，自动调用合适工具 |
| **响应速度** | 规则匹配毫秒级，不用等LLM推理 |
| **功能丰富** | 支持订单、商品、FAQ、人工转接等多种场景 |
| **容错机制** | 工具执行失败时优雅降级 |
| **业务价值** | 自动化处理常见问题，节省人工成本 |

**产品化设计案例**：

```python
# 案例1：用户体验 - 智能工具选择
"""
用户说："我在淘宝买的手机到哪了？"
↓ Agent自动识别：
  - 平台：taobao
  - 意图：查物流
  - 工具：query_ecommerce_order
↓ 用户不需要知道具体API，只需说人话
↓ 结果：对话自然，体验流畅
"""

# 案例2：业务价值 - 自动化率提升
"""
传统客服：
- 80%的问题需要人工处理
- 客服响应慢，成本高

Agent客服：
- 60%的问题自动处理
- 15%的问题由Agent+工具处理
- 25%的问题转人工
↓ 结果：人工成本降低70%
"""

# 案例3：容错机制 - 优雅降级
def execute_with_fallback(tool_name, **kwargs):
    try:
        # 尝试主要工具
        return primary_tool.execute(**kwargs)
    except Exception as e:
        # 降级到备用方案
        return fallback_tool.execute(**kwargs)
```

---

## 7.11 本章小结

### 核心概念

- ✅ **Agent** = 感知 → 决策 → 执行
- ✅ **工具系统** = 基类 + 注册表 + 执行器
- ✅ **规则选择** = 快速、可靠的工具决策
- ✅ **数据提供层** = 工具与数据源解耦

### 关键文件

| 文件 | 作用 |
|------|------|
| [agent_system.py](../../chat-service/agent_system.py) | Agent执行器 |
| [tools/core/registry.py](../../chat-service/tools/core/registry.py) | 工具注册表 |
| [tools/core/base.py](../../chat-service/tools/core/base.py) | 工具基类 |
| [tools/tool_definitions/*.py](../../chat-service/tools/tool_definitions) | 具体工具 |

### 下一步学习

- [08_工具注册系统.md](./08_工具注册系统.md) - 深入工具系统
- [09_电商工具集成.md](./09_电商工具集成.md) - 电商工具详解
- [10_意图路由系统.md](./10_意图路由系统.md) - 意图识别
