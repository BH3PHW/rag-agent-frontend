"""
商品信息查询工具
"""
from typing import Dict, Any
from ..core.base import BaseTool, Parameter, ToolResult


class ProductInfoTool(BaseTool):
    """商品信息查询工具"""
    
    name = "query_product"
    description = "查询商品信息"
    tool_type = "DATA_QUERY"
    
    parameters = [
        Parameter(
            name="product_name",
            type="string",
            description="商品名称",
            required=False
        ),
        Parameter(
            name="product_id",
            type="string",
            description="商品编号",
            required=False
        )
    ]
    
    def execute(self, **kwargs) -> ToolResult:
        product_id = kwargs.get("product_id")
        product_name = kwargs.get("product_name")
        
        if product_id:
            product = self.data_provider.get_product(product_id)
            if product:
                return ToolResult(
                    success=True,
                    data=product
                )
            return ToolResult(
                success=False,
                error=f"商品 {product_id} 未找到"
            )
        
        if product_name:
            products = self.data_provider.search_products(product_name)
            if products:
                return ToolResult(
                    success=True,
                    data=products[0] if len(products) == 1 else products
                )
            return ToolResult(
                success=False,
                error=f"未找到名称包含 '{product_name}' 的商品"
            )
        
        return ToolResult(
            success=False,
            error="请提供商品编号或商品名称"
        )


class ProductSearchTool(BaseTool):
    """商品搜索工具"""
    
    name = "search_products"
    description = "搜索商品"
    tool_type = "DATA_QUERY"
    
    parameters = [
        Parameter(
            name="keyword",
            type="string",
            description="搜索关键词",
            required=True
        )
    ]
    
    def execute(self, **kwargs) -> ToolResult:
        keyword = kwargs.get("keyword", "")
        
        if not keyword:
            return ToolResult(
                success=False,
                error="请提供搜索关键词"
            )
        
        products = self.data_provider.search_products(keyword)
        
        return ToolResult(
            success=True,
            data={
                "keyword": keyword,
                "count": len(products),
                "products": products
            }
        )
