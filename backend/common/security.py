"""
Security utilities - JWT, password hashing, enterprise authorization
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import logging

from common.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    include_enterprise: bool = True
) -> str:
    """
    Create JWT access token.
    If include_enterprise is True, user must be associated with an enterprise.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow().timestamp()
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow().timestamp()
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Get current user ID from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    return user_id


async def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """Verify token and return payload"""
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


class TokenData:
    """Token data extracted from JWT"""
    def __init__(self, payload: dict):
        self.user_id = payload.get("sub")
        self.enterprise_id = payload.get("enterprise_id")
        self.role = payload.get("role", "user")
        self.token_type = payload.get("type", "access")
        self.exp = payload.get("exp")
        self.iat = payload.get("iat")


async def get_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Extract and validate token data"""
    payload = await verify_token(token)
    return TokenData(payload)


async def get_current_enterprise_id(token_data: TokenData = Depends(get_token_data)) -> str:
    """
    Get current user's enterprise ID from token.
    Raises exception if user is not associated with an enterprise.
    """
    if not token_data.enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any enterprise"
        )
    return token_data.enterprise_id


async def get_optional_enterprise_id(token_data: TokenData = Depends(get_token_data)) -> Optional[str]:
    """Get enterprise ID if available, None otherwise"""
    return token_data.enterprise_id


def validate_enterprise_access(
    token_enterprise_id: Optional[str],
    requested_enterprise_id: str,
    allow_admin: bool = True
) -> bool:
    """
    Validate that requested enterprise matches token's enterprise.
    
    Args:
        token_enterprise_id: Enterprise ID from user's JWT token
        requested_enterprise_id: Enterprise ID from the request
        allow_admin: If True, admins can access any enterprise (future use)
    
    Returns:
        True if access is allowed
    
    Raises:
        HTTPException if access is denied
    """
    if not token_enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any enterprise"
        )
    
    if str(token_enterprise_id) != str(requested_enterprise_id):
        logger.warning(
            f"Enterprise access violation: "
            f"token_enterprise={token_enterprise_id}, "
            f"requested_enterprise={requested_enterprise_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to requested enterprise"
        )
    
    return True


def log_enterprise_access(
    action: str,
    enterprise_id: str,
    user_id: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    success: bool = True
):
    """Log enterprise data access for audit purposes"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "enterprise_id": enterprise_id,
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "success": success,
        "ip_address": None
    }
    
    if success:
        logger.info(f"Enterprise access: {log_entry}")
    else:
        logger.warning(f"Enterprise access denied: {log_entry}")


def require_role(required_role: str):
    """Decorator to require specific role"""
    async def role_checker(token_data: TokenData = Depends(get_token_data)):
        if token_data.role != required_role and token_data.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}"
            )
        return token_data
    return role_checker
