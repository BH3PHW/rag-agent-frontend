"""
User Service - 用户与企业管理系统
==================================

主要功能：
- 用户管理：注册、登录、认证、权限
- 企业管理：创建企业、企业配置、企业成员
- 敏感词管理：敏感词设置、语义规则配置
- 多租户隔离：确保企业间数据完全隔离

安全特性：
- JWT认证：Token中包含企业ID，实现企业级权限控制
- 密码加密：bcrypt哈希算法
- 企业隔离：每个用户只能访问自己企业的数据
"""

# FastAPI核心框架
from fastapi import FastAPI, Depends, HTTPException, status, Request
# 密码哈希工具
from passlib.context import CryptContext
# JWT认证
from jose import JWTError, jwt
# 日期时间处理
from datetime import datetime, timedelta
# SQLAlchemy ORM
from sqlalchemy.orm import Session
from sqlalchemy import or_
# typing类型提示
from typing import Optional, List
from uuid import UUID
# Pydantic数据验证
from pydantic import BaseModel, EmailStr, Field

# 导入配置
from .config import settings
# 导入数据库连接
from .database import get_db, init_db
# 导入Redis客户端
from .redis_client import redis_manager

# 导入角色管理路由
from .role_endpoints import router as role_router

# 注册角色管理路由
app.include_router(role_router)

# 导入数据模型
from .models import User, Enterprise, SensitiveSettings, SemanticRule


# 创建密码哈希上下文，使用bcrypt算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 创建FastAPI应用
app = FastAPI(
    title="User Service",
    description="User and Enterprise Management Service",
    version="1.0.0"
)


# ==================== 数据模型 ====================

class UserCreate(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class EnterpriseCreate(BaseModel):
    """企业创建请求模型"""
    name: str = Field(..., min_length=2, max_length=100)


class SensitiveSettingsUpdate(BaseModel):
    """敏感词设置更新模型"""
    enable_keyword_detection: bool = True
    enable_semantic_detection: bool = True
    sensitive_words: List[str] = []
    human_required_categories: List[str] = []


class SemanticRuleCreate(BaseModel):
    """语义规则创建模型"""
    category: str
    keywords: List[str]
    description: str = ""
    enabled: bool = True
    requires_human: bool = False


# ==================== 辅助函数 ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    将用户输入的明文密码与数据库中的哈希密码进行比对

    参数:
        plain_password: 明文密码
        hashed_password: 哈希密码

    返回:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    使用bcrypt算法对密码进行哈希处理

    参数:
        password: 明文密码

    返回:
        哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    生成JWT访问令牌，包含用户ID和企业ID

    参数:
        data: 要编码的数据（包含sub:用户ID, enterprise_id:企业ID）
        expires_delta: 过期时间增量

    返回:
        JWT令牌字符串
    """
    to_encode = data.copy()

    # 设置过期时间，默认为15分钟
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    创建刷新令牌

    生成JWT刷新令牌，有效期更长（7天）

    参数:
        data: 要编码的数据

    返回:
        JWT刷新令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    验证JWT令牌

    解码并验证JWT令牌的有效性

    参数:
        token: JWT令牌

    返回:
        令牌载荷数据，如果无效则返回None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "user-service"}


@app.get("/")
async def root():
    """根路径"""
    return {"service": "User Service", "version": "1.0.0"}


# ==================== 认证端点 ====================

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册

    创建新用户账号，自动创建关联企业

    参数:
        user: 用户注册信息（用户名、邮箱、密码）
        db: 数据库会话

    返回:
        认证令牌

    异常:
        HTTPException 400: 用户名或邮箱已存在
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 创建用户
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(new_user)
    db.flush()  # 获取用户ID

    # 自动创建关联企业
    enterprise = Enterprise(
        name=f"{user.username}'s Enterprise",
        owner_id=new_user.id
    )
    db.add(enterprise)
    db.flush()  # 获取企业ID

    # 更新用户的企业ID
    new_user.enterprise_id = enterprise.id
    db.commit()
    db.refresh(new_user)

    # 创建令牌
    access_token = create_access_token({
        "sub": str(new_user.id),
        "enterprise_id": str(enterprise.id)
    })
    refresh_token = create_refresh_token({
        "sub": str(new_user.id)
    })

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    验证用户名密码，返回认证令牌

    参数:
        credentials: 登录凭据（用户名、密码）
        db: 数据库会话

    返回:
        认证令牌

    异常:
        HTTPException 401: 用户名或密码错误
    """
    # 查找用户
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # 验证密码
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )

    # 创建令牌
    access_token = create_access_token({
        "sub": str(user.id),
        "enterprise_id": str(user.enterprise_id) if user.enterprise_id else None
    })
    refresh_token = create_refresh_token({
        "sub": str(user.id)
    })

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/api/v1/auth/logout")
async def logout():
    """
    用户登出

    清除认证状态（Token在客户端清除）

    返回:
        成功消息
    """
    return {"message": "Logout successful"}


@app.get("/api/v1/auth/me")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息

    从请求头中获取Token，解析并返回当前用户信息

    参数:
        request: HTTP请求对象
        db: 数据库会话

    返回:
        当前用户信息

    异常:
        HTTPException 401: 未认证或Token无效
    """
    # 从请求头获取Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # 提取Token
    token = auth_header.split(" ")[1]

    # 验证Token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # 从Token获取用户ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # 查询用户信息
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )

    return {
        "user_id": str(user.id),
        "user_name": user.username,
        "user_email": user.email,
        "user_role": user.role,
        "enterprise_id": str(user.enterprise_id) if user.enterprise_id else None,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    获取用户信息

    根据用户ID获取用户详细信息

    参数:
        user_id: 用户ID
        db: 数据库会话

    返回:
        用户信息
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "enterprise_id": str(user.enterprise_id) if user.enterprise_id else None,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


# ==================== 企业管理端点 ====================

@app.post("/api/v1/enterprises")
async def create_enterprise(
    data: EnterpriseCreate,
    db: Session = Depends(get_db),
    current_user_id: str = None
):
    """
    创建企业

    创建新的租户企业

    参数:
        data: 企业信息（名称）
        db: 数据库会话
        current_user_id: 当前用户ID（从Token中提取）

    返回:
        创建的企业信息
    """
    enterprise = Enterprise(
        name=data.name,
        owner_id=UUID(current_user_id) if current_user_id else None
    )
    db.add(enterprise)
    db.commit()
    db.refresh(enterprise)

    return {
        "id": str(enterprise.id),
        "name": enterprise.name,
        "created_at": enterprise.created_at.isoformat() if enterprise.created_at else None
    }


@app.get("/api/v1/enterprises/{enterprise_id}")
async def get_enterprise(enterprise_id: UUID, db: Session = Depends(get_db)):
    """
    获取企业信息

    根据企业ID获取企业详细信息

    参数:
        enterprise_id: 企业ID
        db: 数据库会话

    返回:
        企业信息
    """
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(status_code=404, detail="Enterprise not found")

    return {
        "id": str(enterprise.id),
        "name": enterprise.name,
        "api_key": enterprise.api_key,
        "qwen_model": enterprise.qwen_model,
        "created_at": enterprise.created_at.isoformat() if enterprise.created_at else None
    }


@app.put("/api/v1/enterprises/{enterprise_id}")
async def update_enterprise(
    enterprise_id: UUID,
    data: EnterpriseCreate,
    db: Session = Depends(get_db)
):
    """
    更新企业信息

    更新指定企业的名称等信息

    参数:
        enterprise_id: 企业ID
        data: 更新的企业信息（名称）
        db: 数据库会话

    返回:
        更新后的企业信息

    异常:
        HTTPException 404: 企业不存在
    """
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(status_code=404, detail="Enterprise not found")

    enterprise.name = data.name
    db.commit()
    db.refresh(enterprise)

    return {
        "id": str(enterprise.id),
        "name": enterprise.name,
        "api_key": enterprise.api_key,
        "qwen_model": enterprise.qwen_model,
        "created_at": enterprise.created_at.isoformat() if enterprise.created_at else None
    }


@app.delete("/api/v1/enterprises/{enterprise_id}")
async def delete_enterprise(enterprise_id: UUID, db: Session = Depends(get_db)):
    """
    删除企业

    删除指定的企业及其关联数据

    参数:
        enterprise_id: 企业ID
        db: 数据库会话

    返回:
        删除成功消息

    异常:
        HTTPException 404: 企业不存在
    """
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(status_code=404, detail="Enterprise not found")

    db.delete(enterprise)
    db.commit()

    return {"message": "Enterprise deleted successfully"}


# ==================== 敏感词设置端点 ====================

@app.get("/api/v1/enterprises/{enterprise_id}/sensitive-settings")
async def get_sensitive_settings(enterprise_id: UUID, db: Session = Depends(get_db)):
    """
    获取敏感词设置

    获取企业的敏感内容检测配置

    参数:
        enterprise_id: 企业ID
        db: 数据库会话

    返回:
        敏感词设置配置
    """
    settings_obj = db.query(SensitiveSettings).filter(
        SensitiveSettings.enterprise_id == enterprise_id
    ).first()

    if not settings_obj:
        # 如果不存在，返回默认设置
        return {
            "enable_keyword_detection": True,
            "enable_semantic_detection": True,
            "sensitive_words": [],
            "human_required_categories": [],
            "semantic_rules": []
        }

    # 获取语义规则
    rules = db.query(SemanticRule).filter(
        SemanticRule.enterprise_id == enterprise_id,
        SemanticRule.enabled == True
    ).all()

    return {
        "enable_keyword_detection": settings_obj.enable_keyword_detection,
        "enable_semantic_detection": settings_obj.enable_semantic_detection,
        "sensitive_words": settings_obj.sensitive_words or [],
        "human_required_categories": settings_obj.human_required_categories or [],
        "semantic_rules": [
            {
                "id": str(rule.id),
                "category": rule.category,
                "keywords": rule.keywords or [],
                "description": rule.description or "",
                "enabled": rule.enabled,
                "requires_human": rule.requires_human
            }
            for rule in rules
        ]
    }


@app.put("/api/v1/enterprises/{enterprise_id}/sensitive-settings")
async def update_sensitive_settings(
    enterprise_id: UUID,
    data: SensitiveSettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    更新敏感词设置

    修改企业的敏感内容检测配置

    参数:
        enterprise_id: 企业ID
        data: 新的配置数据
        db: 数据库会话

    返回:
        更新后的敏感词设置
    """
    settings_obj = db.query(SensitiveSettings).filter(
        SensitiveSettings.enterprise_id == enterprise_id
    ).first()

    if not settings_obj:
        # 创建新设置
        settings_obj = SensitiveSettings(enterprise_id=enterprise_id)
        db.add(settings_obj)

    # 更新字段
    settings_obj.enable_keyword_detection = data.enable_keyword_detection
    settings_obj.enable_semantic_detection = data.enable_semantic_detection
    settings_obj.sensitive_words = data.sensitive_words
    settings_obj.human_required_categories = data.human_required_categories

    db.commit()
    db.refresh(settings_obj)

    return {
        "enable_keyword_detection": settings_obj.enable_keyword_detection,
        "enable_semantic_detection": settings_obj.enable_semantic_detection,
        "sensitive_words": settings_obj.sensitive_words or [],
        "human_required_categories": settings_obj.human_required_categories or []
    }


@app.post("/api/v1/enterprises/{enterprise_id}/semantic-rules")
async def create_semantic_rule(
    enterprise_id: UUID,
    data: SemanticRuleCreate,
    db: Session = Depends(get_db)
):
    """
    创建语义规则

    添加新的语义检测规则

    参数:
        enterprise_id: 企业ID
        data: 规则配置
        db: 数据库会话

    返回:
        创建的规则信息
    """
    rule = SemanticRule(
        enterprise_id=enterprise_id,
        category=data.category,
        keywords=data.keywords,
        description=data.description,
        enabled=data.enabled,
        requires_human=data.requires_human
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return {
        "id": str(rule.id),
        "category": rule.category,
        "keywords": rule.keywords or [],
        "description": rule.description or "",
        "enabled": rule.enabled,
        "requires_human": rule.requires_human
    }


@app.delete("/api/v1/enterprises/{enterprise_id}/semantic-rules/{rule_id}")
async def delete_semantic_rule(
    enterprise_id: UUID,
    rule_id: UUID,
    db: Session = Depends(get_db)
):
    """
    删除语义规则

    移除指定的语义检测规则

    参数:
        enterprise_id: 企业ID
        rule_id: 规则ID
        db: 数据库会话
    """
    rule = db.query(SemanticRule).filter(
        SemanticRule.id == rule_id,
        SemanticRule.enterprise_id == enterprise_id
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()

    return {"message": "Rule deleted"}


# ==================== 生命周期管理 ====================

@app.on_event("startup")
async def startup():
    """应用启动初始化"""
    print("User Service starting up...")
    init_db()
    print("Database initialized")
    await redis_manager.connect()
    print("Redis connected")
    print("User Service ready!")


@app.on_event("shutdown")
async def shutdown():
    """应用关闭清理"""
    print("User Service shutting down...")
    await redis_manager.disconnect()
