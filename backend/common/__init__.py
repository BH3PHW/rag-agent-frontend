"""
Common utilities package
"""

from common.config import settings
from common.database import get_db, Base, engine, init_db
from common.redis_client import redis_manager, get_redis
from common.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user_id,
    verify_token,
    TokenData,
    get_token_data,
    get_current_enterprise_id,
    get_optional_enterprise_id,
    validate_enterprise_access,
    log_enterprise_access,
    require_role
)

__all__ = [
    "settings",
    "get_db",
    "Base",
    "engine",
    "init_db",
    "redis_manager",
    "get_redis",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user_id",
    "verify_token",
    "TokenData",
    "get_token_data",
    "get_current_enterprise_id",
    "get_optional_enterprise_id",
    "validate_enterprise_access",
    "log_enterprise_access",
    "require_role"
]
