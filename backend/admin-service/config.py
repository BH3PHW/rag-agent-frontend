"""
Admin-Service Configuration
基于common配置模块
"""
import os
import sys
from pathlib import Path
from functools import lru_cache

# 添加backend根目录到Python路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

# 使用common配置
try:
    from common.config import CommonSettings
except ImportError as e:
    print(f"Warning: Could not import CommonSettings: {e}")
    # 如果导入失败，使用pydantic-settings作为基础
    from pydantic_settings import BaseSettings
    CommonSettings = BaseSettings


class Settings(CommonSettings):
    """Admin-Service Service settings - 继承通用配置"""
    
    # ========== 应用基本配置 ==========
    APP_NAME: str = "Admin-Service Service"
    APP_VERSION: str = "1.0.0"
    
    # ========== 数据库配置 ==========
    # 数据库连接URL，格式：postgresql://用户名:密码@主机:端口/数据库名
    # 测试环境使用SQLite，生产环境必须使用ADMIN_SERVICE_DATABASE_URL环境变量覆盖
    DATABASE_URL: str = os.getenv(
        "ADMIN_SERVICE_DATABASE_URL",
        os.getenv("DATABASE_URL", "sqlite:////tmp/rag_admin.db")
    )
    
    # ========== Redis配置 ==========
    # Redis连接URL，格式：redis://主机:端口/数据库号
    # 用于缓存、会话管理等
    REDIS_URL: str = os.getenv("ADMIN_SERVICE_REDIS_URL", "redis://localhost:6379/2")
    
    # ========== JWT安全配置 ==========
    # JWT密钥，生产环境必须使用强随机密钥
    SECRET_KEY: str = os.getenv("ADMIN_SERVICE_SECRET_KEY", os.getenv("SECRET_KEY", "admin-service-secret-key"))
    # JWT加密算法
    ALGORITHM: str = "HS256"
    # 访问令牌过期时间（分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # 刷新令牌过期时间（天）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ========== CORS跨域配置 ==========
    # 允许的跨域来源，生产环境应设置具体域名而不是"*"
    CORS_ORIGINS: list = ["*"]
    
    # ========== 微服务通信配置 ==========
    # 聊天服务URL，用于调用聊天相关的管理API
    CHAT_SERVICE_URL: str = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8002")
    # 分析服务URL，用于调用数据分析和统计API
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8007")
    # 告警服务URL，用于调用告警管理API
    ALERT_SERVICE_URL: str = os.getenv("ALERT_SERVICE_URL", "http://alert-service:8004")
    # 知识库服务URL，用于调用知识库管理API
    KNOWLEDGE_SERVICE_URL: str = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8003")
    
    # ========== HTTP客户端配置 ==========
    # HTTP请求超时时间（秒）
    HTTP_TIMEOUT: float = 10.0
    
    # ========== 客服坐席配置 ==========
    # 坐席默认最大并发会话数
    AGENT_DEFAULT_MAX_CONCURRENT: int = 5
    # 坐席会话等待超时时间（秒）
    AGENT_SESSION_WAIT_TIMEOUT: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


settings = get_settings()
