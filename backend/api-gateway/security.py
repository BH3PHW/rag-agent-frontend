"""
API Gateway Security Utilities
"""
from typing import Optional, Dict, Any
from jose import JWTError, jwt

from .config import settings


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    return decode_token(token)


def validate_enterprise_access(token_enterprise_id: str, request_enterprise_id: str) -> bool:
    """
    Validate that the request is authorized to access the enterprise.
    """
    if str(token_enterprise_id) != str(request_enterprise_id):
        raise ValueError("Enterprise access denied")
    return True
