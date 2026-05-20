"""
渠道接入层 - 主服务
统一消息协议 + OneID + 适配器 + 渲染器
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import httpx
import json

from .config import settings
from .database import get_db, init_db
from .redis_client import get_redis, close_redis
from .models import (
    ChannelConfig, 
    EnterpriseChannelAccount,
    ChannelAccessLog,
    EcommercePlatformConfig
)
from .ecommerce_service import EcommercePlatformService
from .protocols import (
    UnifiedMessage, PlatformMessage,
    PlatformType, MessageDirection
)
from .adapters import get_adapter
from .renderers import get_renderer, render_message
from .oneid import OneIDService, SessionMappingService
import time
from datetime import datetime, timedelta
from sqlalchemy import func


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await get_redis()
    yield
    await close_redis()


app = FastAPI(
    title="Channel Service",
    description="渠道接入层 - 统一消息协议 + OneID + 多渠道适配",
    version=settings.APP_VERSION,
    lifespan=lifespan
)


def log_channel_access(
    db: Session,
    enterprise_id: str,
    channel_type: str,
    log_type: str,
    action: Optional[str] = None,
    request_data: Optional[Dict] = None,
    response_data: Optional[Dict] = None,
    error_message: Optional[str] = None,
    duration_ms: Optional[int] = None,
    ip_address: Optional[str] = None,
    channel_account_id: Optional[str] = None
):
    """记录渠道接入日志"""
    try:
        log = ChannelAccessLog(
            enterprise_id=enterprise_id,
            channel_account_id=channel_account_id,
            channel_type=channel_type,
            log_type=log_type,
            action=action,
            request_data=request_data,
            response_data=response_data,
            error_message=error_message,
            status="failed" if error_message else "success",
            duration_ms=duration_ms,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Failed to log channel access: {e}")


def get_channel_config(db: Session, enterprise_id: str, channel_type: str) -> Dict[str, Any]:
    """获取渠道配置"""
    # 优先从企业渠道账户获取
    account = db.query(EnterpriseChannelAccount).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id,
        EnterpriseChannelAccount.channel_type == channel_type,
        EnterpriseChannelAccount.is_active == True
    ).first()
    
    if account:
        return {
            "app_id": account.app_id,
            "app_secret": account.app_secret,
            "token": account.token,
            "aes_key": account.aes_key,
            "extra_config": account.extra_config or {},
            "account_id": account.id
        }
    
    # 回退到旧的 ChannelConfig
    config = db.query(ChannelConfig).filter(
        ChannelConfig.enterprise_id == enterprise_id,
        ChannelConfig.channel_type == channel_type,
        ChannelConfig.is_active == True
    ).first()
    
    if not config:
        return {
            "app_id": "",
            "app_secret": "",
            "token": "",
            "aes_key": ""
        }
    
    return {
        "app_id": config.app_id,
        "app_secret": config.app_secret,
        "token": config.token,
        "aes_key": config.aes_key,
        "extra_config": config.extra_config or {}
    }


def update_channel_stats(
    db: Session,
    enterprise_id: str,
    channel_type: str,
    message_count: int = 1,
    user_count: int = 0
):
    """更新渠道统计信息"""
    try:
        account = db.query(EnterpriseChannelAccount).filter(
            EnterpriseChannelAccount.enterprise_id == enterprise_id,
            EnterpriseChannelAccount.channel_type == channel_type,
            EnterpriseChannelAccount.is_active == True
        ).first()
        
        if account:
            account.message_count = (account.message_count or 0) + message_count
            account.user_count = (account.user_count or 0) + user_count
            account.last_message_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        print(f"Failed to update channel stats: {e}")


@app.post("/api/v1/channel/{enterprise_id}/{platform_type}/webhook")
async def receive_webhook(
    enterprise_id: str,
    platform_type: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    接收各平台的 Webhook 消息入口
    """
    start_time = time.time()
    ip_address = request.client.host if request.client else None
    
    try:
        platform_type_enum = PlatformType(platform_type)
    except ValueError:
        # 记录错误日志
        duration_ms = int((time.time() - start_time) * 1000)
        log_channel_access(
            db, enterprise_id, platform_type, "error",
            action="validate_platform_type",
            error_message=f"Unsupported platform: {platform_type}",
            duration_ms=duration_ms,
            ip_address=ip_address
        )
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform_type}")
    
    body = await request.body()
    
    config = get_channel_config(db, enterprise_id, platform_type)
    adapter = get_adapter(platform_type_enum, config)
    
    valid = adapter.validate_signature(request)
    if not valid:
        # 记录签名验证失败
        duration_ms = int((time.time() - start_time) * 1000)
        log_channel_access(
            db, enterprise_id, platform_type, "error",
            action="validate_signature",
            error_message="Invalid signature",
            duration_ms=duration_ms,
            ip_address=ip_address,
            channel_account_id=config.get("account_id")
        )
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        if platform_type_enum in [PlatformType.WECHAT]:
            raw_data = body
        else:
            raw_data = json.loads(body.decode('utf-8'))
    except Exception:
        raw_data = body
    
    platform_msg = PlatformMessage(
        platform_type=platform_type_enum,
        raw_data=raw_data,
        enterprise_id=enterprise_id
    )
    
    unified_msg = adapter.parse(platform_msg)
    
    oneid_service = OneIDService(db)
    unified_msg = oneid_service.enrich_message(unified_msg)
    
    result = await process_inbound_message(unified_msg, db)
    
    # 记录成功日志
    duration_ms = int((time.time() - start_time) * 1000)
    log_channel_access(
        db, enterprise_id, platform_type, "webhook",
        action="receive_message",
        request_data={"content": unified_msg.content},
        response_data=result,
        duration_ms=duration_ms,
        ip_address=ip_address,
        channel_account_id=config.get("account_id")
    )
    
    # 更新统计信息
    update_channel_stats(db, enterprise_id, platform_type, message_count=1)
    
    return result


@app.post("/api/v1/channel/{enterprise_id}/message")
async def receive_direct_message(
    enterprise_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    直接接收统一格式消息
    """
    data = await request.json()
    
    unified_msg = UnifiedMessage(**data)
    
    if not unified_msg.enterprise_id:
        unified_msg.enterprise_id = enterprise_id
    
    oneid_service = OneIDService(db)
    unified_msg = oneid_service.enrich_message(unified_msg)
    
    return await process_inbound_message(unified_msg, db)


async def process_inbound_message(msg: UnifiedMessage, db: Session):
    """处理入站消息"""
    from datetime import datetime
    
    session_service = SessionMappingService(db)
    platform_session = session_service.get_or_create_platform_session(
        enterprise_id=msg.enterprise_id,
        platform_type=msg.platform_type,
        platform_session_id=msg.platform_session_id or msg.platform_user_id,
        unified_user_id=msg.unified_user_id,
        chat_session_id=msg.chat_session_id
    )
    
    if not platform_session.chat_session_id:
        chat_session_id = await create_chat_session(msg)
        platform_session.chat_session_id = chat_session_id
        db.commit()
    
    msg.chat_session_id = platform_session.chat_session_id
    
    response = await call_chat_service(
        session_id=msg.chat_session_id,
        enterprise_id=msg.enterprise_id,
        user_id=msg.unified_user_id,
        content=msg.content
    )
    
    if response and isinstance(response, dict) and "content" in response:
        reply_msg = UnifiedMessage(
            message_id=msg.message_id,
            enterprise_id=msg.enterprise_id,
            unified_user_id=msg.unified_user_id,
            platform_type=msg.platform_type,
            platform_user_id=msg.platform_user_id,
            platform_session_id=msg.platform_session_id,
            chat_session_id=msg.chat_session_id,
            direction=MessageDirection.OUTBOUND,
            content=response["content"],
            original_message=response
        )
        
        rendered = render_message(reply_msg)
        
        return {
            "success": True,
            "unified_user_id": msg.unified_user_id,
            "chat_session_id": msg.chat_session_id,
            "reply": rendered.content,
            "reply_format": rendered.message_type
        }
    
    return {
        "success": True,
        "unified_user_id": msg.unified_user_id,
        "chat_session_id": msg.chat_session_id
    }


async def create_chat_session(msg: UnifiedMessage) -> str:
    """创建内部聊天会话"""
    url = f"{settings.CHAT_SERVICE_URL}/api/v1/chat/sessions"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={
                "enterprise_id": msg.enterprise_id,
                "user_id": msg.unified_user_id
            }
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("session_id") or str(data.get("id"))
    return f"fallback_session_{msg.unified_user_id}"


async def call_chat_service(session_id: str, enterprise_id: str, user_id: str, content: str):
    """调用聊天服务"""
    url = f"{settings.CHAT_SERVICE_URL}/api/v1/chat/sessions/{session_id}/messages/stream"
    
    full_content = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            json={
                "content": content,
                "enterprise_id": enterprise_id,
                "user_id": user_id
            }
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        if "content" in data:
                            full_content.append(data["content"])
                    except:
                        pass
    
    return {"content": "".join(full_content)}


@app.get("/api/v1/channel/{enterprise_id}/oneid/mappings")
async def get_oneid_mappings(
    enterprise_id: str,
    unified_user_id: str,
    db: Session = Depends(get_db)
):
    """获取 OneID 映射"""
    oneid_service = OneIDService(db)
    mappings = oneid_service.get_mappings(enterprise_id, unified_user_id)
    return {
        "unified_user_id": unified_user_id,
        "mappings": [
            {
                "platform_type": m.platform_type,
                "platform_user_id": m.platform_user_id,
                "phone": m.phone
            }
            for m in mappings
        ]
    }


@app.post("/api/v1/channel/{enterprise_id}/oneid/link-phone")
async def link_phone(
    enterprise_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """关联手机号到 OneID"""
    data = await request.json()
    oneid_service = OneIDService(db)
    oneid_service.link_phone(
        enterprise_id=enterprise_id,
        unified_user_id=data["unified_user_id"],
        phone=data["phone"]
    )
    return {"success": True}


@app.post("/api/v1/channel/{enterprise_id}/oneid/link-crm")
async def link_crm(
    enterprise_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """关联 CRM ID 到 OneID"""
    data = await request.json()
    oneid_service = OneIDService(db)
    oneid_service.link_crm_id(
        enterprise_id=enterprise_id,
        unified_user_id=data["unified_user_id"],
        crm_user_id=data["crm_user_id"]
    )
    return {"success": True}


@app.post("/api/v1/channel/{enterprise_id}/config")
async def set_channel_config(
    enterprise_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """设置渠道配置"""
    data = await request.json()
    
    existing = db.query(ChannelConfig).filter(
        ChannelConfig.enterprise_id == enterprise_id,
        ChannelConfig.channel_type == data["channel_type"]
    ).first()
    
    if existing:
        existing.app_id = data.get("app_id")
        existing.app_secret = data.get("app_secret")
        existing.token = data.get("token")
        existing.aes_key = data.get("aes_key")
        existing.extra_config = data.get("extra_config")
    else:
        config = ChannelConfig(
            enterprise_id=enterprise_id,
            channel_type=data["channel_type"],
            app_id=data.get("app_id"),
            app_secret=data.get("app_secret"),
            token=data.get("token"),
            aes_key=data.get("aes_key"),
            extra_config=data.get("extra_config")
        )
        db.add(config)
    
    db.commit()
    
    return {"success": True}


@app.get("/api/v1/channel/{enterprise_id}/configs")
async def get_channel_configs(
    enterprise_id: str,
    db: Session = Depends(get_db)
):
    """获取所有渠道配置"""
    configs = db.query(ChannelConfig).filter(
        ChannelConfig.enterprise_id == enterprise_id
    ).all()
    
    return {
        "configs": [
            {
                "channel_type": c.channel_type,
                "is_active": c.is_active
            }
            for c in configs
        ]
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "channel-service"}


@app.get("/")
async def root():
    return {
        "service": "Channel Service",
        "version": settings.APP_VERSION,
        "platforms": [p.value for p in PlatformType]
    }


# ========== 企业客户渠道管理 API ==========

@app.get("/api/v1/channel/{enterprise_id}/accounts")
async def list_channel_accounts(
    enterprise_id: str,
    channel_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """列出企业的所有渠道账户"""
    query = db.query(EnterpriseChannelAccount).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id
    )
    
    if channel_type:
        query = query.filter(EnterpriseChannelAccount.channel_type == channel_type)
    
    if status:
        query = query.filter(EnterpriseChannelAccount.status == status)
    
    accounts = query.order_by(
        EnterpriseChannelAccount.is_active.desc(),
        EnterpriseChannelAccount.updated_at.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "total": len(accounts),
        "accounts": [
            {
                "id": a.id,
                "channel_name": a.channel_name,
                "channel_type": a.channel_type,
                "status": a.status,
                "is_active": a.is_active,
                "message_count": a.message_count,
                "user_count": a.user_count,
                "last_message_at": a.last_message_at.isoformat() if a.last_message_at else None,
                "webhook_url": a.webhook_url,
                "description": a.description,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat()
            }
            for a in accounts
        ]
    }


@app.get("/api/v1/channel/{enterprise_id}/accounts/{account_id}")
async def get_channel_account(
    enterprise_id: str,
    account_id: str,
    db: Session = Depends(get_db)
):
    """获取单个渠道账户详情"""
    account = db.query(EnterpriseChannelAccount).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id,
        EnterpriseChannelAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Channel account not found")
    
    return {
        "id": account.id,
        "channel_name": account.channel_name,
        "channel_type": account.channel_type,
        "status": account.status,
        "is_active": account.is_active,
        "app_id": account.app_id,
        # 不返回敏感信息
        "token": "***" if account.token else None,
        "aes_key": "***" if account.aes_key else None,
        "extra_config": account.extra_config,
        "webhook_url": account.webhook_url,
        "webhook_secret": "***" if account.webhook_secret else None,
        "message_count": account.message_count,
        "user_count": account.user_count,
        "last_message_at": account.last_message_at.isoformat() if account.last_message_at else None,
        "description": account.description,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat()
    }


@app.post("/api/v1/channel/{enterprise_id}/accounts")
async def create_channel_account(
    enterprise_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """创建渠道账户"""
    data = await request.json()
    
    required_fields = ["channel_name", "channel_type"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # 验证渠道类型
    try:
        PlatformType(data["channel_type"])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid channel type: {data['channel_type']}")
    
    # 生成 webhook URL
    import secrets
    webhook_secret = secrets.token_urlsafe(32)
    webhook_url = f"{request.url.scheme}://{request.url.netloc}/api/v1/channel/{enterprise_id}/{data['channel_type']}/webhook"
    
    account = EnterpriseChannelAccount(
        enterprise_id=enterprise_id,
        channel_name=data["channel_name"],
        channel_type=data["channel_type"],
        status="draft",
        app_id=data.get("app_id"),
        app_secret=data.get("app_secret"),
        token=data.get("token"),
        aes_key=data.get("aes_key"),
        extra_config=data.get("extra_config"),
        webhook_url=webhook_url,
        webhook_secret=webhook_secret,
        description=data.get("description")
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return {
        "success": True,
        "account_id": account.id,
        "webhook_url": webhook_url,
        "webhook_secret": webhook_secret
    }


@app.put("/api/v1/channel/{enterprise_id}/accounts/{account_id}")
async def update_channel_account(
    enterprise_id: str,
    account_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """更新渠道账户"""
    data = await request.json()
    
    account = db.query(EnterpriseChannelAccount).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id,
        EnterpriseChannelAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Channel account not found")
    
    # 更新字段
    if "channel_name" in data:
        account.channel_name = data["channel_name"]
    if "description" in data:
        account.description = data["description"]
    if "app_id" in data:
        account.app_id = data["app_id"]
    if "app_secret" in data:
        account.app_secret = data["app_secret"]
    if "token" in data:
        account.token = data["token"]
    if "aes_key" in data:
        account.aes_key = data["aes_key"]
    if "extra_config" in data:
        account.extra_config = data["extra_config"]
    
    db.commit()
    
    return {"success": True}


@app.post("/api/v1/channel/{enterprise_id}/accounts/{account_id}/activate")
async def activate_channel_account(
    enterprise_id: str,
    account_id: str,
    db: Session = Depends(get_db)
):
    """激活渠道账户"""
    account = db.query(EnterpriseChannelAccount).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id,
        EnterpriseChannelAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Channel account not found")
    
    account.is_active = True
    account.status = "active"
    db.commit()
    
    return {"success": True, "status": "active"}


@app.post("/api/v1/channel/{enterprise_id}/accounts/{account_id}/deactivate")
async def deactivate_channel_account(
    enterprise_id: str,
    account_id: str,
    db: Session = Depends(get_db)
):
    """停用渠道账户"""
    account = db.query(EnterpriseChannelAccount).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id,
        EnterpriseChannelAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Channel account not found")
    
    account.is_active = False
    account.status = "inactive"
    db.commit()
    
    return {"success": True, "status": "inactive"}


@app.delete("/api/v1/channel/{enterprise_id}/accounts/{account_id}")
async def delete_channel_account(
    enterprise_id: str,
    account_id: str,
    db: Session = Depends(get_db)
):
    """删除渠道账户（软删除）"""
    account = db.query(EnterpriseChannelAccount).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id,
        EnterpriseChannelAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Channel account not found")
    
    account.is_active = False
    account.status = "inactive"
    db.commit()
    
    return {"success": True}


@app.get("/api/v1/channel/{enterprise_id}/accounts/{account_id}/logs")
async def get_channel_access_logs(
    enterprise_id: str,
    account_id: str,
    log_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取渠道接入日志"""
    query = db.query(ChannelAccessLog).filter(
        ChannelAccessLog.enterprise_id == enterprise_id,
        ChannelAccessLog.channel_account_id == account_id
    )
    
    if log_type:
        query = query.filter(ChannelAccessLog.log_type == log_type)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(ChannelAccessLog.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(ChannelAccessLog.created_at <= end_dt)
        except ValueError:
            pass
    
    logs = query.order_by(
        ChannelAccessLog.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "total": len(logs),
        "logs": [
            {
                "id": l.id,
                "log_type": l.log_type,
                "action": l.action,
                "status": l.status,
                "error_message": l.error_message,
                "duration_ms": l.duration_ms,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat()
            }
            for l in logs
        ]
    }


@app.post("/api/v1/channel/{enterprise_id}/accounts/{account_id}/test")
async def test_channel_connection(
    enterprise_id: str,
    account_id: str,
    db: Session = Depends(get_db)
):
    """测试渠道连接"""
    account = db.query(EnterpriseChannelAccount).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id,
        EnterpriseChannelAccount.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Channel account not found")
    
    # 这里可以根据不同渠道类型实现具体的连接测试
    test_result = {
        "success": True,
        "channel_type": account.channel_type,
        "tested_at": datetime.utcnow().isoformat(),
        "checks": {
            "config_exists": bool(account.app_id or account.token),
            "webhook_configured": bool(account.webhook_url)
        }
    }
    
    return test_result


@app.get("/api/v1/channel/{enterprise_id}/stats/overview")
async def get_channel_stats(
    enterprise_id: str,
    db: Session = Depends(get_db)
):
    """获取企业渠道统计概览"""
    # 总账户数
    total_accounts = db.query(func.count(EnterpriseChannelAccount.id)).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id
    ).scalar() or 0
    
    # 活跃账户数
    active_accounts = db.query(func.count(EnterpriseChannelAccount.id)).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id,
        EnterpriseChannelAccount.is_active == True
    ).scalar() or 0
    
    # 各渠道分布
    channel_stats = db.query(
        EnterpriseChannelAccount.channel_type,
        func.count(EnterpriseChannelAccount.id),
        func.sum(EnterpriseChannelAccount.message_count)
    ).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id
    ).group_by(EnterpriseChannelAccount.channel_type).all()
    
    # 总消息数
    total_messages = db.query(func.sum(EnterpriseChannelAccount.message_count)).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id
    ).scalar() or 0
    
    # 总用户数
    total_users = db.query(func.sum(EnterpriseChannelAccount.user_count)).filter(
        EnterpriseChannelAccount.enterprise_id == enterprise_id
    ).scalar() or 0
    
    return {
        "overview": {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "total_messages": total_messages,
            "total_users": total_users
        },
        "channel_distribution": [
            {
                "channel_type": cs[0],
                "account_count": cs[1],
                "message_count": cs[2] or 0
            }
            for cs in channel_stats
        ]
    }


@app.get("/api/v1/channel/platforms")
async def get_supported_platforms():
    """获取支持的平台列表和配置说明"""
    platforms_config = [
        {
            "type": "web",
            "name": "网页 Widget",
            "description": "嵌入网页的聊天 Widget",
            "setup_fields": ["widget_id", "theme"],
            "docs_url": "https://docs.example.com/channel/web"
        },
        {
            "type": "wechat",
            "name": "微信公众号",
            "description": "微信公众号自动回复",
            "setup_fields": ["app_id", "app_secret", "token", "aes_key"],
            "docs_url": "https://docs.example.com/channel/wechat"
        },
        {
            "type": "wechat_miniprogram",
            "name": "微信小程序",
            "description": "微信小程序客服",
            "setup_fields": ["app_id", "app_secret"],
            "docs_url": "https://docs.example.com/channel/wechat-miniprogram"
        },
        {
            "type": "douyin",
            "name": "抖音",
            "description": "抖音私信客服",
            "setup_fields": ["app_key", "app_secret"],
            "docs_url": "https://docs.example.com/channel/douyin"
        },
        {
            "type": "dingtalk",
            "name": "钉钉",
            "description": "钉钉群聊机器人",
            "setup_fields": ["app_key", "app_secret", "robot_code"],
            "docs_url": "https://docs.example.com/channel/dingtalk"
        },
        {
            "type": "feishu",
            "name": "飞书",
            "description": "飞书智能助手",
            "setup_fields": ["app_id", "app_secret"],
            "docs_url": "https://docs.example.com/channel/feishu"
        },
        {
            "type": "sms",
            "name": "短信",
            "description": "短信客服通知",
            "setup_fields": ["api_key", "signature"],
            "docs_url": "https://docs.example.com/channel/sms"
        },
        {
            "type": "email",
            "name": "邮件",
            "description": "邮件客服处理",
            "setup_fields": ["smtp_host", "smtp_port", "username", "password"],
            "docs_url": "https://docs.example.com/channel/email"
        }
    ]
    
    return {
        "platforms": platforms_config
    }


# ========== 电商平台管理 API ==========

@app.get("/api/v1/ecommerce/{enterprise_id}/platforms")
async def list_ecommerce_platforms(
    enterprise_id: str,
    db: Session = Depends(get_db)
):
    """列出企业的所有电商平台配置"""
    service = EcommercePlatformService(db)
    platforms = service.list_platforms(enterprise_id)
    return {
        "total": len(platforms),
        "platforms": [
            {
                "id": p.id,
                "platform_type": p.platform_type,
                "store_id": p.store_id,
                "store_name": p.store_name,
                "is_active": p.is_active,
                "sync_orders": p.sync_orders,
                "sync_products": p.sync_products,
                "auto_reply": p.auto_reply,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat()
            }
            for p in platforms
        ]
    }


@app.get("/api/v1/ecommerce/{enterprise_id}/platforms/{platform_id}")
async def get_ecommerce_platform(
    enterprise_id: str,
    platform_id: str,
    db: Session = Depends(get_db)
):
    """获取单个电商平台配置详情"""
    service = EcommercePlatformService(db)
    platform = service.get_platform(enterprise_id, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Ecommerce platform not found")
    return {
        "id": platform.id,
        "platform_type": platform.platform_type,
        "store_id": platform.store_id,
        "store_name": platform.store_name,
        "app_key": platform.app_key,
        "app_secret": "***" if platform.app_secret else None,
        "access_token": "***" if platform.access_token else None,
        "refresh_token": "***" if platform.refresh_token else None,
        "is_active": platform.is_active,
        "sync_orders": platform.sync_orders,
        "sync_products": platform.sync_products,
        "auto_reply": platform.auto_reply,
        "extra_config": platform.extra_config,
        "last_sync_at": platform.last_sync_at.isoformat() if platform.last_sync_at else None,
        "created_at": platform.created_at.isoformat(),
        "updated_at": platform.updated_at.isoformat()
    }


@app.post("/api/v1/ecommerce/{enterprise_id}/platforms")
async def create_ecommerce_platform(
    enterprise_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """创建电商平台配置"""
    data = await request.json()
    
    required_fields = ["platform_type", "store_id", "store_name"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    service = EcommercePlatformService(db)
    platform = service.create_platform(enterprise_id, data)
    
    return {
        "success": True,
        "platform_id": platform.id
    }


@app.put("/api/v1/ecommerce/{enterprise_id}/platforms/{platform_id}")
async def update_ecommerce_platform(
    enterprise_id: str,
    platform_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """更新电商平台配置"""
    data = await request.json()
    
    service = EcommercePlatformService(db)
    platform = service.update_platform(enterprise_id, platform_id, data)
    
    if not platform:
        raise HTTPException(status_code=404, detail="Ecommerce platform not found")
    
    return {"success": True}


@app.delete("/api/v1/ecommerce/{enterprise_id}/platforms/{platform_id}")
async def delete_ecommerce_platform(
    enterprise_id: str,
    platform_id: str,
    db: Session = Depends(get_db)
):
    """删除电商平台配置"""
    service = EcommercePlatformService(db)
    success = service.delete_platform(enterprise_id, platform_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Ecommerce platform not found")
    
    return {"success": True}


@app.post("/api/v1/ecommerce/{enterprise_id}/platforms/{platform_id}/test")
async def test_ecommerce_platform_connection(
    enterprise_id: str,
    platform_id: str,
    db: Session = Depends(get_db)
):
    """测试电商平台连接"""
    service = EcommercePlatformService(db)
    result = service.test_platform_connection(enterprise_id, platform_id)
    return result


@app.get("/api/v1/ecommerce/{enterprise_id}/platforms/{platform_id}/orders")
async def get_ecommerce_platform_orders(
    enterprise_id: str,
    platform_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取电商平台订单"""
    service = EcommercePlatformService(db)
    orders = service.get_platform_orders(enterprise_id, platform_id, limit)
    return {
        "total": len(orders),
        "orders": orders
    }


@app.get("/api/v1/ecommerce/{enterprise_id}/platforms/{platform_id}/products")
async def get_ecommerce_platform_products(
    enterprise_id: str,
    platform_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取电商平台商品"""
    service = EcommercePlatformService(db)
    products = service.get_platform_products(enterprise_id, platform_id, limit)
    return {
        "total": len(products),
        "products": products
    }


@app.get("/api/v1/ecommerce/available-platforms")
async def get_available_ecommerce_platforms():
    """获取支持的电商平台列表"""
    service = EcommercePlatformService(None)
    platforms = service.get_available_platforms()
    return {"platforms": platforms}


# ========== 电商平台 API 配置管理 ==========

@app.get("/api/v1/ecommerce/{enterprise_id}/platforms/{platform_id}/api-config")
async def get_ecommerce_platform_api_config(
    enterprise_id: str,
    platform_id: str,
    db: Session = Depends(get_db)
):
    """获取平台 API 配置"""
    service = EcommercePlatformService(db)
    config = service.get_platform_api_config(platform_id, enterprise_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="平台配置不存在")
    
    return {"success": True, "api_config": config}


@app.put("/api/v1/ecommerce/{enterprise_id}/platforms/{platform_id}/api-config")
async def update_ecommerce_platform_api_config(
    enterprise_id: str,
    platform_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """更新平台 API 配置"""
    data = await request.json()
    
    service = EcommercePlatformService(db)
    platform = service.update_platform_api_config(platform_id, enterprise_id, data)
    
    if not platform:
        raise HTTPException(status_code=404, detail="平台配置不存在")
    
    return {"success": True, "message": "API 配置更新成功"}


@app.post("/api/v1/ecommerce/{enterprise_id}/platforms/{platform_id}/api-config/reset")
async def reset_ecommerce_platform_api_config(
    enterprise_id: str,
    platform_id: str,
    db: Session = Depends(get_db)
):
    """重置平台 API 配置为默认值"""
    service = EcommercePlatformService(db)
    platform = service.reset_platform_api_config(platform_id, enterprise_id)
    
    if not platform:
        raise HTTPException(status_code=404, detail="平台配置不存在")
    
    return {"success": True, "message": "API 配置已重置为默认值"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "channel_service.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True
    )
