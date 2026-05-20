"""
User Service Database
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
    
    # 创建User Service专用的数据库管理器
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
