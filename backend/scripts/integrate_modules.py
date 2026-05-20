#!/usr/bin/env python3
"""
通用模块整合脚本
将服务整合到common模块
"""
import os
from pathlib import Path
import shutil


def integrate_service(service_name: str):
    """整合单个服务"""
    service_path = Path(f"/workspace/backend/{service_name}")
    
    if not service_path.exists():
        print(f"❌ {service_name} 不存在")
        return
    
    print(f"\n{'='*60}")
    print(f"整合 {service_name}")
    print('='*60)
    
    # 1. 整合 config.py
    config_file = service_path / "config.py"
    if config_file.exists():
        print(f"\n1. 整合 config.py")
        
        new_config = f'''"""
{service_name.title()} Configuration
基于common配置模块
"""
import os
from functools import lru_cache

# 使用common配置
try:
    from common.config import CommonSettings
except ImportError:
    CommonSettings = None


class Settings(CommonSettings):
    """{service_name.title()} Service settings - 继承通用配置"""
    
    APP_NAME: str = "{service_name.title()} Service"
    APP_VERSION: str = "1.0.0"
    
    # 使用环境变量前缀以支持多服务隔离
    DATABASE_URL: str = os.getenv(
        "{service_name.upper()}_DATABASE_URL",
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/{service_name}")
    )
    
    REDIS_URL: str = os.getenv("{service_name.upper()}_REDIS_URL", "redis://localhost:6379/2")
    
    # JWT配置（复用通用配置）
    SECRET_KEY: str = os.getenv("{service_name.upper()}_SECRET_KEY", os.getenv("SECRET_KEY", "{service_name}-secret-key"))
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
'''
        
        # 备份原文件
        backup_file = config_file.with_suffix('.py.bak')
        shutil.copy(config_file, backup_file)
        print(f"  ✅ 已备份到 {backup_file}")
        
        # 写入新文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(new_config)
        print(f"  ✅ 已整合 config.py")
    
    # 2. 整合 database.py
    db_file = service_path / "database.py"
    if db_file.exists():
        print(f"\n2. 整合 database.py")
        
        new_db = f'''"""
{service_name.title()} Service Database
使用common.database模块
"""
import sys
from pathlib import Path
from typing import Generator

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

# 尝试使用common.database
try:
    from common.database import DatabaseManager, get_db as common_get_db, init_db as common_init_db
    from .config import settings
    
    # 创建{service_name.title()} Service专用的数据库管理器
    _db_manager = None
    
    def get_db() -> Generator:
        """获取数据库会话"""
        global _db_manager
        if _db_manager is None:
            _db_manager = DatabaseManager(
                database_url=settings.DATABASE_URL,
                pool_size=10,
                max_overflow=20
            )
        return common_get_db(_db_manager)
    
    def init_db():
        """初始化数据库"""
        global _db_manager
        if _db_manager is None:
            _db_manager = DatabaseManager(
                database_url=settings.DATABASE_URL,
                pool_size=10,
                max_overflow=20
            )
        return common_init_db(_db_manager)

except (ImportError, AttributeError):
    # 如果common.database不可用，使用本地实现
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, declarative_base
    from .config import settings
    
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        echo=False
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    def get_db() -> Generator:
        """获取数据库会话"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def init_db():
        """初始化数据库"""
        Base.metadata.create_all(bind=engine)
'''
        
        # 备份原文件
        backup_file = db_file.with_suffix('.py.bak')
        shutil.copy(db_file, backup_file)
        print(f"  ✅ 已备份到 {backup_file}")
        
        # 写入新文件
        with open(db_file, 'w', encoding='utf-8') as f:
            f.write(new_db)
        print(f"  ✅ 已整合 database.py")
    
    # 3. 整合 redis_client.py
    redis_file = service_path / "redis_client.py"
    if redis_file.exists():
        print(f"\n3. 整合 redis_client.py")
        
        new_redis = f'''"""
{service_name.title()} Service Redis Client
使用common.redis_client模块
"""
import sys
from pathlib import Path

# 添加backend根目录到路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

# 尝试使用common.redis_client
try:
    from common.redis_client import RedisManager, redis_manager as common_redis_manager
    from .config import settings
    
    # 创建{service_name.title()} Service专用的Redis管理器
    _redis_manager = None
    
    def get_redis_manager() -> RedisManager:
        """获取Redis管理器"""
        global _redis_manager
        if _redis_manager is None:
            _redis_manager = RedisManager()
        return _redis_manager
    
    redis_manager = get_redis_manager()
    
    # 设置正确的Redis URL
    redis_manager.redis_url = settings.REDIS_URL
    redis_manager.password = settings.REDIS_PASSWORD

except (ImportError, AttributeError):
    # 如果common.redis_client不可用，使用本地实现
    import redis.asyncio as redis
    from typing import Optional
    
    class RedisManager:
        """Redis connection manager"""
        
        def __init__(self):
            self._redis: Optional[redis.Redis] = None
            self.redis_url = "redis://localhost:6379/2"
            self.password = None
        
        async def connect(self):
            """Connect to Redis"""
            if self._redis is None:
                self._redis = await redis.from_url(
                    self.redis_url,
                    password=self.password,
                    decode_responses=True
                )
            return self._redis
        
        async def disconnect(self):
            """Disconnect from Redis"""
            if self._redis is not None:
                await self._redis.close()
                self._redis = None
        
        async def get(self, key: str) -> Optional[str]:
            """Get value from Redis"""
            r = await self.connect()
            return await r.get(key)
        
        async def set(self, key: str, value: str, expire: int = None):
            """Set value in Redis"""
            r = await self.connect()
            await r.set(key, value, ex=expire)
        
        async def delete(self, key: str):
            """Delete key from Redis"""
            r = await self.connect()
            await r.delete(key)
        
        async def incr(self, key: str) -> int:
            """Increment value"""
            r = await self.connect()
            return await r.incr(key)
        
        async def expire(self, key: str, seconds: int):
            """Set expiration"""
            r = await self.connect()
            await r.expire(key, seconds)
    
    redis_manager = RedisManager()
'''
        
        # 备份原文件
        backup_file = redis_file.with_suffix('.py.bak')
        shutil.copy(redis_file, backup_file)
        print(f"  ✅ 已备份到 {backup_file}")
        
        # 写入新文件
        with open(redis_file, 'w', encoding='utf-8') as f:
            f.write(new_redis)
        print(f"  ✅ 已整合 redis_client.py")
    
    print(f"\n✅ {service_name} 整合完成！")
    print(f"   原文件已备份为 .py.bak")


def main():
    """整合所有服务"""
    print("\n" + "="*60)
    print("通用模块整合脚本")
    print("="*60)
    
    # 要整合的服务列表
    services = [
        "alert-service",
        "analytics-service",
        "admin-service"
    ]
    
    for service in services:
        integrate_service(service)
    
    print("\n" + "="*60)
    print("所有服务整合完成！")
    print("="*60)
    
    print("\n后续步骤：")
    print("1. 测试各服务是否正常运行")
    print("2. 如果需要回滚，可以将 .py.bak 文件恢复")
    print("3. 清理不需要的备份文件")


if __name__ == "__main__":
    main()
