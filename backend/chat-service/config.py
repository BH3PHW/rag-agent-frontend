"""
Chat Service Configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Chat Service settings"""
    
    # Application
    APP_NAME: str = "Chat Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/rag_service"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # ChromaDB
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
    
    # Qwen API
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
    QWEN_API_ENDPOINT: str = os.getenv(
        "QWEN_API_ENDPOINT", 
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    )
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen-turbo")
    QWEN_TEMPERATURE: float = 0.7
    QWEN_MAX_TOKENS: int = 2000
    
    # RAG Settings
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Rerank Settings
    RERANK_ENABLED: bool = os.getenv("RERANK_ENABLED", "true").lower() == "true"
    RERANK_USE_CROSS_ENCODER: bool = os.getenv("RERANK_USE_CROSS_ENCODER", "true").lower() == "true"
    
    # Sensitive Words
    SENSITIVE_KEYWORDS: list = [
        "投诉", "举报", "诈骗", "欺诈", "违法", "犯罪",
        "退款", "退货", "赔偿", "律师", "法院", "警察",
        "上访", "自杀", "暴力", "恐怖", "色情", "赌博",
        "毒品", "武器", "机密", "泄密", "不满", "愤怒",
        "控诉", "起诉", "投诉", "很差", "失望", "坑人"
    ]
    
    # Alert Settings
    ALERT_ENABLED: bool = True
    HUMAN_THRESHOLD: int = 3
    
    # Knowledge Service API
    KNOWLEDGE_SERVICE_URL: str = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8002")
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
