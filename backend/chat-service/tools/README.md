# 解耦工具系统架构

## 概述

这是一个可扩展、解耦的工具系统架构，用于替代 built_in_tools.py 中的硬编码实现。

**注意：当前系统主要使用 built_in_tools.py 和 tool_system.py，此架构为未来改进的参考设计。**

## 架构优势

1. **关注点分离**：数据提供与工具逻辑分离
2. **易于测试**：使用依赖注入的模拟数据
3. **易于扩展**：添加新工具不需要修改核心代码
4. **自动发现**：工具可以自动被发现和注册
5. **向后兼容**：设计支持与现有系统并存

## 目录结构

```
tools/
├── __init__.py              # 入口模块
├── README.md                # 本文件
├── core/
│   ├── __init__.py
│   ├── base.py              # 基类定义（BaseTool, DataProvider等）
│   ├── registry.py          # 工具注册表（向后兼容）
│   └── loader.py            # 工具发现和加载
├── data_providers/
│   ├── __init__.py
│   ├── mock_provider.py     # 模拟数据提供器
│   └── ecommerce_provider.py # 电商数据提供器
└── tool_definitions/
    ├── __init__.py
    ├── order_tool.py        # 订单查询工具
    ├── product_tool.py      # 商品信息工具
    ├── kb_search_tool.py    # 知识库搜索工具
    ├── human_transfer_tool.py # 人工转接工具
    ├── faq_tool.py          # FAQ查询工具
    ├── ecommerce_order_tool.py   # 电商订单工具
    ├── ecommerce_product_tool.py # 电商商品工具
    └── ecommerce_platform_tool.py # 电商平台工具
```

## 使用说明

### 如何在未来完全迁移

1. 在 main.py 中，将 agent_system.py 的实现替换为使用此架构
2. 更新 loader.py 的导入路径，使其与项目结构兼容
3. 测试所有工具功能正常工作后，可以安全删除 built_in_tools.py 的硬编码数据
