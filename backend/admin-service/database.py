"""
Admin-Service Database Module
提供数据库连接和会话管理
"""
import sys
from pathlib import Path
from typing import Generator

# 添加backend根目录到Python路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
try:
    from .config import settings
except ImportError:
    from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
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
    """初始化数据库表"""
    # 导入models确保表被创建
    try:
        from admin_service.models import Agent, AgentSession
    except ImportError:
        try:
            from models import Agent, AgentSession
        except ImportError:
            pass
    Base.metadata.create_all(bind=engine)
