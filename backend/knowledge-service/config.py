"""
Knowledge Service Configuration
使用 common 模块的通用配置
"""
import os
import sys
from pathlib import Path
from functools import lru_cache

# 添加backend根目录到Python路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

try:
    from common.config import CommonSettings
except ImportError:
    from pydantic_settings import BaseSettings
    CommonSettings = BaseSettings


class Settings(CommonSettings):
    """Knowledge Service settings - 继承通用配置"""
    
    APP_NAME: str = "Knowledge Service"
    
    # 使用环境变量前缀以支持多服务隔离
    DATABASE_URL: str = os.getenv(
        "KNOWLEDGE_DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/knowledge_service")
    )
    
    REDIS_URL: str = os.getenv("KNOWLEDGE_REDIS_URL", "redis://localhost:6379/0")
    
    SECRET_KEY: str = os.getenv("KNOWLEDGE_SECRET_KEY", os.getenv("SECRET_KEY", "knowledge-service-secret-key"))


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()