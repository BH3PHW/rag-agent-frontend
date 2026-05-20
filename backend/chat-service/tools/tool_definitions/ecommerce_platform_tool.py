"""
电商平台管理工具
"""
from ..core.base import BaseTool, Parameter, ToolResult


class EcommercePlatformTool(BaseTool):
    """电商平台管理工具"""
    
    name = "list_ecommerce_platforms"
    description = "获取电商平台列表和状态"
    tool_type = "DATA_QUERY"
    
    parameters = [
        Parameter(
            name="platform_id",
            type="string",
            description="平台ID(可选，不提供则返回所有平台)",
            required=False
        )
    ]
    
    def execute(self, **kwargs) -> ToolResult:
        platform_id = kwargs.get("platform_id")
        
        if hasattr(self.data_provider, 'get_platforms'):
            platforms = self.data_provider.get_platforms()
            
            if platform_id:
                platform = next(
                    (p for p in platforms if p["id"] == platform_id),
                    None
                )
                if platform:
                    return ToolResult(
                        success=True,
                        data=platform
                    )
                return ToolResult(
                    success=False,
                    error=f"平台 {platform_id} 未找到"
                )
            
            return ToolResult(
                success=True,
                data={
                    "count": len(platforms),
                    "platforms": platforms
                }
            )
        
        # 回退到默认平台列表
        default_platforms = [
            {"id": "taobao", "name": "淘宝/天猫", "enabled": True},
            {"id": "jd", "name": "京东", "enabled": True},
            {"id": "pdd", "name": "拼多多", "enabled": True},
            {"id": "douyin", "name": "抖音商城", "enabled": True},
            {"id": "xianyu", "name": "闲鱼", "enabled": True},
            {"id": "xiaohongshu", "name": "小红书", "enabled": True}
        ]
        
        if platform_id:
            platform = next(
                (p for p in default_platforms if p["id"] == platform_id),
                None
            )
            if platform:
                return ToolResult(success=True, data=platform)
            return ToolResult(success=False, error=f"平台 {platform_id} 未找到")
        
        return ToolResult(
            success=True,
            data={
                "count": len(default_platforms),
                "platforms": default_platforms
            }
        )
