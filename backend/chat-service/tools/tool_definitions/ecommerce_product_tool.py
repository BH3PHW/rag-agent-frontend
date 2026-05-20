"""
电商商品查询工具
"""
from ..core.base import BaseTool, Parameter, ToolResult


class EcommerceProductTool(BaseTool):
    """电商商品查询工具"""
    
    name = "query_ecommerce_product"
    description = "查询电商平台商品"
    tool_type = "DATA_QUERY"
    
    parameters = [
        Parameter(
            name="platform_type",
            type="string",
            description="电商平台(可选)",
            required=False
        ),
        Parameter(
            name="platform",
            type="string",
            description="电商平台(可选，同platform_type)",
            required=False
        ),
        Parameter(
            name="product_id",
            type="string",
            description="商品编号(可选)",
            required=False
        ),
        Parameter(
            name="product_name",
            type="string",
            description="商品名称(可选)",
            required=False
        ),
        Parameter(
            name="keyword",
            type="string",
            description="搜索关键词(可选)",
            required=False
        )
    ]
    
    def execute(self, **kwargs) -> ToolResult:
        platform = kwargs.get("platform_type") or kwargs.get("platform")
        product_id = kwargs.get("product_id")
        product_name = kwargs.get("product_name")
        keyword = kwargs.get("keyword") or product_name
        
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
        
        if keyword:
            products = self.data_provider.search_products(keyword)
            # 如果指定了平台，可进一步过滤
            if platform:
                products = [
                    p for p in products
                    if p.get("platform") == platform
                ]
            return ToolResult(
                success=True,
                data={
                    "keyword": keyword,
                    "platform": platform,
                    "count": len(products),
                    "products": products
                }
            )
        
        return ToolResult(
            success=False,
            error="请提供商品编号或搜索关键词"
        )
