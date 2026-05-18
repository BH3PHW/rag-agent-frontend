"""
渠道接入层 - OneID 统一身份识别
将不同平台的用户 ID 映射到统一的 unified_user_id
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from .models import OneIDMapping, PlatformSession
from .protocols import UnifiedMessage, PlatformType
import uuid


class OneIDService:
    """OneID 统一身份服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_unified_user(
        self,
        enterprise_id: str,
        platform_type: PlatformType,
        platform_user_id: str,
        phone: Optional[str] = None,
        unionid: Optional[str] = None,
        openid: Optional[str] = None,
        crm_user_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """获取或创建统一用户ID
        
        优先查找策略：
        1. 先查平台+用户ID的映射
        2. 再查手机号关联
        3. 查UnionID关联
        4. 查CRM ID关联
        5. 如果都没找到，创建新的
        """
        mapping = None
        
        # 1. 查平台用户映射
        mapping = self._query_by_platform(enterprise_id, platform_type, platform_user_id)
        if mapping:
            return mapping.unified_user_id
        
        # 2. 查手机号关联
        if phone:
            mapping = self._query_by_phone(enterprise_id, phone)
            if mapping:
                self._add_platform_mapping(
                    mapping.unified_user_id, enterprise_id,
                    platform_type, platform_user_id,
                    phone=phone, unionid=unionid, openid=openid, crm_user_id=crm_user_id
                )
                return mapping.unified_user_id
        
        # 3. 查UnionID关联
        if unionid:
            mapping = self._query_by_unionid(enterprise_id, unionid)
            if mapping:
                self._add_platform_mapping(
                    mapping.unified_user_id, enterprise_id,
                    platform_type, platform_user_id,
                    phone=phone, unionid=unionid, openid=openid, crm_user_id=crm_user_id
                )
                return mapping.unified_user_id
        
        # 4. 查CRM ID关联
        if crm_user_id:
            mapping = self._query_by_crm_id(enterprise_id, crm_user_id)
            if mapping:
                self._add_platform_mapping(
                    mapping.unified_user_id, enterprise_id,
                    platform_type, platform_user_id,
                    phone=phone, unionid=unionid, openid=openid, crm_user_id=crm_user_id
                )
                return mapping.unified_user_id
        
        # 5. 创建新的统一用户
        unified_user_id = self._generate_unified_user_id()
        
        self._add_platform_mapping(
            unified_user_id, enterprise_id,
            platform_type, platform_user_id,
            phone=phone, unionid=unionid, openid=openid, crm_user_id=crm_user_id,
            extra_data=extra_data
        )
        
        return unified_user_id
    
    def _query_by_platform(
        self, enterprise_id: str, platform_type: PlatformType, platform_user_id: str
    ) -> Optional[OneIDMapping]:
        """按平台+用户ID查询"""
        return self.db.query(OneIDMapping).filter(
            OneIDMapping.enterprise_id == enterprise_id,
            OneIDMapping.platform_type == platform_type,
            OneIDMapping.platform_user_id == platform_user_id
        ).first()
    
    def _query_by_phone(
        self, enterprise_id: str, phone: str
    ) -> Optional[OneIDMapping]:
        """按手机号查询"""
        return self.db.query(OneIDMapping).filter(
            OneIDMapping.enterprise_id == enterprise_id,
            OneIDMapping.phone == phone
        ).first()
    
    def _query_by_unionid(
        self, enterprise_id: str, unionid: str
    ) -> Optional[OneIDMapping]:
        """按UnionID查询"""
        return self.db.query(OneIDMapping).filter(
            OneIDMapping.enterprise_id == enterprise_id,
            OneIDMapping.unionid == unionid
        ).first()
    
    def _query_by_crm_id(
        self, enterprise_id: str, crm_user_id: str
    ) -> Optional[OneIDMapping]:
        """按CRM ID查询"""
        return self.db.query(OneIDMapping).filter(
            OneIDMapping.enterprise_id == enterprise_id,
            OneIDMapping.crm_user_id == crm_user_id
        ).first()
    
    def _add_platform_mapping(
        self,
        unified_user_id: str,
        enterprise_id: str,
        platform_type: PlatformType,
        platform_user_id: str,
        phone: Optional[str] = None,
        unionid: Optional[str] = None,
        openid: Optional[str] = None,
        crm_user_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """添加平台映射"""
        existing = self._query_by_platform(enterprise_id, platform_type, platform_user_id)
        if existing:
            return existing
        
        mapping = OneIDMapping(
            unified_user_id=unified_user_id,
            enterprise_id=enterprise_id,
            platform_type=platform_type,
            platform_user_id=platform_user_id,
            phone=phone,
            unionid=unionid,
            openid=openid,
            crm_user_id=crm_user_id,
            extra_data=extra_data
        )
        self.db.add(mapping)
        self.db.commit()
        return mapping
    
    def _generate_unified_user_id(self) -> str:
        """生成统一用户ID"""
        return f"u_{uuid.uuid4().hex[:16]}"
    
    def link_phone(
        self, enterprise_id: str, unified_user_id: str, phone: str
    ):
        """关联手机号"""
        mappings = self.db.query(OneIDMapping).filter(
            OneIDMapping.enterprise_id == enterprise_id,
            OneIDMapping.unified_user_id == unified_user_id
        ).all()
        
        for mapping in mappings:
            if not mapping.phone:
                mapping.phone = phone
        
        self.db.commit()
    
    def link_crm_id(
        self, enterprise_id: str, unified_user_id: str, crm_user_id: str
    ):
        """关联CRM ID"""
        mappings = self.db.query(OneIDMapping).filter(
            OneIDMapping.enterprise_id == enterprise_id,
            OneIDMapping.unified_user_id == unified_user_id
        ).all()
        
        for mapping in mappings:
            if not mapping.crm_user_id:
                mapping.crm_user_id = crm_user_id
        
        self.db.commit()
    
    def get_mappings(
        self, enterprise_id: str, unified_user_id: str
    ):
        """获取用户的所有平台映射"""
        return self.db.query(OneIDMapping).filter(
            OneIDMapping.enterprise_id == enterprise_id,
            OneIDMapping.unified_user_id == unified_user_id
        ).all()
    
    def enrich_message(self, msg: UnifiedMessage) -> UnifiedMessage:
        """为消息补充 OneID 信息"""
        if msg.unified_user_id:
            return msg
        
        phone = msg.extra_data.get("phone")
        unionid = msg.extra_data.get("unionid")
        openid = msg.extra_data.get("openid")
        crm_user_id = msg.extra_data.get("crm_user_id")
        
        unified_user_id = self.get_or_create_unified_user(
            enterprise_id=msg.enterprise_id,
            platform_type=msg.platform_type,
            platform_user_id=msg.platform_user_id,
            phone=phone,
            unionid=unionid,
            openid=openid,
            crm_user_id=crm_user_id,
            extra_data=msg.extra_data
        )
        
        msg.unified_user_id = unified_user_id
        return msg


class SessionMappingService:
    """渠道会话映射服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_platform_session(
        self,
        enterprise_id: str,
        platform_type: PlatformType,
        platform_session_id: str,
        unified_user_id: str,
        chat_session_id: Optional[str] = None
    ) -> PlatformSession:
        """获取或创建平台会话"""
        session = self.db.query(PlatformSession).filter(
            PlatformSession.enterprise_id == enterprise_id,
            PlatformSession.platform_type == platform_type,
            PlatformSession.platform_session_id == platform_session_id
        ).first()
        
        if session:
            if chat_session_id and not session.chat_session_id:
                session.chat_session_id = chat_session_id
            session.last_message_at = datetime.utcnow()
            self.db.commit()
            return session
        
        session = PlatformSession(
            enterprise_id=enterprise_id,
            platform_type=platform_type,
            platform_session_id=platform_session_id,
            unified_user_id=unified_user_id,
            chat_session_id=chat_session_id
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
