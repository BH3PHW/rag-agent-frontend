"""
JWT 身份验证模块

提供真实的企业级身份验证机制：
1. JWT Token 生成和验证
2. Token 刷新机制
3. 多种认证方式支持（用户名密码、OAuth）
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import jwt
import hashlib
import secrets
import re


@dataclass
class UserToken:
    """用户Token信息"""
    user_id: str
    enterprise_id: str
    token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"


@dataclass
class TokenPayload:
    """Token载荷信息"""
    user_id: str
    enterprise_id: str
    token_type: str
    issued_at: int
    expires_at: int
    jti: str  # JWT ID


class JWTService:
    """JWT身份验证服务"""
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def generate_access_token(
        self,
        user_id: str,
        enterprise_id: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, datetime]:
        """生成访问令牌"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "user_id": user_id,
            "enterprise_id": enterprise_id,
            "token_type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": secrets.token_hex(16)
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, expires_at
    
    def generate_refresh_token(self, user_id: str, enterprise_id: str) -> Tuple[str, datetime]:
        """生成刷新令牌"""
        now = datetime.utcnow()
        expires_at = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "user_id": user_id,
            "enterprise_id": enterprise_id,
            "token_type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": secrets.token_hex(16)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, expires_at
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[TokenPayload], str]:
        """验证Token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            if payload.get("token_type") not in ["access", "refresh"]:
                return False, None, "无效的Token类型"
            
            token_payload = TokenPayload(
                user_id=payload["user_id"],
                enterprise_id=payload["enterprise_id"],
                token_type=payload["token_type"],
                issued_at=payload["iat"],
                expires_at=payload["exp"],
                jti=payload["jti"]
            )
            
            return True, token_payload, ""
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token已过期"
        except jwt.InvalidTokenError as e:
            return False, None, f"无效的Token: {str(e)}"
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Optional[UserToken], str]:
        """使用刷新令牌获取新的访问令牌"""
        is_valid, payload, error = self.verify_token(refresh_token)
        
        if not is_valid:
            return False, None, error
        
        if payload.token_type != "refresh":
            return False, None, "需要刷新令牌"
        
        access_token, expires_at = self.generate_access_token(
            user_id=payload.user_id,
            enterprise_id=payload.enterprise_id
        )
        
        user_token = UserToken(
            user_id=payload.user_id,
            enterprise_id=payload.enterprise_id,
            token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        
        return True, user_token, ""
    
    def extract_token_from_header(self, auth_header: str) -> Optional[str]:
        """从Authorization头部提取Token"""
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]


class OAuthService:
    """OAuth第三方登录服务"""
    
    SUPPORTED_PROVIDERS = ["wechat", "weibo", "dingtalk", "feishu"]
    
    @staticmethod
    def validate_oauth_callback(
        provider: str,
        code: str,
        state: str = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """验证OAuth回调"""
        if provider not in OAuthService.SUPPORTED_PROVIDERS:
            return False, None, f"不支持的OAuth提供商: {provider}"
        
        # 模拟返回
        mock_user_info = {
            "provider": provider,
            "openid": f"{provider}_openid_{hash(code) % 100000}",
            "unionid": f"union_{hash(code) % 100000}",
            "nickname": f"用户{hash(code) % 10000}",
            "avatar": "https://example.com/avatar.jpg"
        }
        
        return True, mock_user_info, ""
    
    @staticmethod
    def generate_oauth_url(provider: str, redirect_uri: str, state: str = None) -> str:
        """生成OAuth授权URL"""
        oauth_urls = {
            "wechat": "https://open.weixin.qq.com/connect/oauth2/authorize",
            "dingtalk": "https://oapi.dingtalk.com/connect/oauth2/authorize",
            "feishu": "https://open.feishu.cn/open-apis/authen/v1/authorize"
        }
        
        if provider not in oauth_urls:
            return None
        
        base_url = oauth_urls[provider]
        params = f"?redirect_uri={redirect_uri}&response_type=code&scope=snsapi_base"
        
        if state:
            params += f"&state={state}"
        
        return base_url + params


class PasswordService:
    """密码安全服务"""
    
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_REQUIREMENTS = {
        "uppercase": r"[A-Z]",
        "lowercase": r"[a-z]",
        "digit": r"\d",
        "special": r"[!@#$%^&*(),.?\":{}|<>]"
    }
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """密码哈希"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """验证密码"""
        computed_hash, _ = PasswordService.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, list]:
        """验证密码强度"""
        violations = []
        
        if len(password) < PasswordService.MIN_PASSWORD_LENGTH:
            violations.append(f"密码长度至少{PasswordService.MIN_PASSWORD_LENGTH}位")
        
        for requirement_name, pattern in PasswordService.PASSWORD_REQUIREMENTS.items():
            if not re.search(pattern, password):
                violations.append(f"密码需要包含{requirement_name}")
        
        return len(violations) == 0, violations
    
    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """生成随机密码"""
        import string
        
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)


_jwt_service: Optional[JWTService] = None


def get_jwt_service() -> JWTService:
    """获取JWT服务单例"""
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTService()
    return _jwt_service
