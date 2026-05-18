"""
CRUD operations for users and enterprises
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .models import User, Enterprise
from .schemas import UserCreate, EnterpriseCreate, UserUpdate, EnterpriseUpdate
from .security import get_password_hash, verify_password


# ============ User CRUD ============

def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    enterprise_id: Optional[UUID] = None
) -> List[User]:
    """Get list of users"""
    query = db.query(User)
    
    if enterprise_id:
        query = query.filter(User.enterprise_id == enterprise_id)
    
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        enterprise_id=user.enterprise_id,
        role="user"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(
    db: Session, 
    user_id: UUID, 
    user_update: UserUpdate
) -> Optional[User]:
    """Update a user"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: UUID) -> bool:
    """Delete a user"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    return user


def update_user_enterprise(db: Session, user_id: UUID, enterprise_id: UUID) -> Optional[User]:
    """Update user's enterprise"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    db_user.enterprise_id = enterprise_id
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user


# ============ Enterprise CRUD ============

def get_enterprise_by_id(db: Session, enterprise_id: UUID) -> Optional[Enterprise]:
    """Get enterprise by ID"""
    return db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()


def get_enterprise_by_api_key(db: Session, api_key: str) -> Optional[Enterprise]:
    """Get enterprise by API key"""
    return db.query(Enterprise).filter(Enterprise.api_key == api_key).first()


def get_enterprises(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[Enterprise]:
    """Get list of enterprises"""
    return db.query(Enterprise).offset(skip).limit(limit).all()


def create_enterprise(db: Session, enterprise: EnterpriseCreate) -> Enterprise:
    """Create a new enterprise"""
    import secrets
    
    db_enterprise = Enterprise(
        name=enterprise.name,
        qwen_model=enterprise.qwen_model,
        sensitive_words=enterprise.sensitive_words,
        api_key=secrets.token_urlsafe(32)
    )
    
    db.add(db_enterprise)
    db.commit()
    db.refresh(db_enterprise)
    return db_enterprise


def update_enterprise(
    db: Session, 
    enterprise_id: UUID, 
    enterprise_update: EnterpriseUpdate
) -> Optional[Enterprise]:
    """Update an enterprise"""
    db_enterprise = get_enterprise_by_id(db, enterprise_id)
    if not db_enterprise:
        return None
    
    update_data = enterprise_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_enterprise, field, value)
    
    db_enterprise.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_enterprise)
    return db_enterprise


def delete_enterprise(db: Session, enterprise_id: UUID) -> bool:
    """Delete an enterprise"""
    db_enterprise = get_enterprise_by_id(db, enterprise_id)
    if not db_enterprise:
        return False
    
    db.delete(db_enterprise)
    db.commit()
    return True


def get_enterprise_users(
    db: Session, 
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[User]:
    """Get all users of an enterprise"""
    return db.query(User).filter(
        User.enterprise_id == enterprise_id
    ).offset(skip).limit(limit).all()


def count_enterprise_users(db: Session, enterprise_id: UUID) -> int:
    """Count users in an enterprise"""
    return db.query(User).filter(
        User.enterprise_id == enterprise_id
    ).count()
