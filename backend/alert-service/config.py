"""
Alert-Service Configuration
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
except ImportError:
    from pydantic_settings import BaseSettings
    CommonSettings = BaseSettings


class Settings(CommonSettings):
    """Alert-Service Service settings - 继承通用配置"""
    
    APP_NAME: str = "Alert-Service Service"
    APP_VERSION: str = "1.0.0"
    
    # 使用环境变量前缀以支持多服务隔离
    DATABASE_URL: str = os.getenv(
        "ALERT-SERVICE_DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alert-service")
    )
    
    REDIS_URL: str = os.getenv("ALERT-SERVICE_REDIS_URL", "redis://localhost:6379/2")
    
    # JWT配置（复用通用配置）
    SECRET_KEY: str = os.getenv("ALERT-SERVICE_SECRET_KEY", os.getenv("SECRET_KEY", "alert-service-secret-key"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


settings = get_settings()
