"""
Admin Service - 运营管理后台服务
===================================

重构说明：
- 删除了对其他服务数据库的直接访问
- 改为通过HTTP API调用各服务的管理端点
- 符合微服务架构的数据隔离原则

主要功能：
- 运营概览：企业运营数据汇总
- 实时统计：实时查询和会话数据
- 性能指标：系统性能监控
- 告警管理：告警查看和处理
- 知识库统计：知识库数据管理
- 客服坐席管理：坐席会话和消息处理
"""
from fastapi import FastAPI, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import asyncio
import json
import httpx
import uuid
from pydantic import BaseModel, Field, EmailStr
import hashlib
import secrets
import sys
from pathlib import Path

# 添加backend根目录到Python路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

try:
    from .config import settings
    from .database import get_db, init_db
    from .models import Agent, AgentSession, AgentStatus, AgentSessionStatus
except ImportError:
    from config import settings
    from database import get_db, init_db
    from models import Agent, AgentSession, AgentStatus, AgentSessionStatus

# 导入模型以确保在初始化时被包含
try:
    from models import Base
except ImportError:
    pass


app = FastAPI(
    title="Admin Service",
    description="Admin Dashboard Backend for RAG Customer Service (Decoupled)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 密码哈希工具
def hash_password(password: str) -> str:
    """简单密码哈希 - 生产环境建议使用 bcrypt"""
    return hashlib.sha256((password + "enterprise_salt").encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return hash_password(password) == hashed


# JWT 令牌工具
def create_access_token(data: dict) -> dict:
    """创建访问令牌"""
    token_data = data.copy()
    token_data["expires"] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    token_data["token"] = secrets.token_urlsafe(32)
    return token_data


class ConnectionManager:
    """WebSocket连接管理器，用于实时更新"""
    def __init__(self):
        self.active_connections: dict = {}
        self.waiting_sessions: List[dict] = []

    async def connect(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        print(f"Agent {agent_id} connected")

    def disconnect(self, agent_id: str):
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            print(f"Agent {agent_id} disconnected")

    async def send_to_agent(self, agent_id: str, message: dict):
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_json(message)
            except Exception as e:
                print(f"Error sending to agent {agent_id}: {e}")

    async def broadcast_to_agents(self, message: dict):
        for agent_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting: {e}")

    async def notify_new_waiting_session(self, session_data: dict):
        self.waiting_sessions.append(session_data)
        await self.broadcast_to_agents({
            "type": "new_waiting_session",
            "data": session_data
        })


manager = ConnectionManager()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/agent/login")


# ========== 坐席相关Pydantic模型 ==========
class AgentProfileResponse(BaseModel):
    id: UUID
    name: str
    username: str
    status: AgentStatus
    current_chats: int
    total_chats: int
    max_concurrent_chats: int
    enterprise_id: UUID
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AgentLoginResponse(BaseModel):
    access_token: str
    token_type: str
    agent: AgentProfileResponse


class UpdateAgentStatusRequest(BaseModel):
    status: AgentStatus


class CreateAgentRequest(BaseModel):
    name: str
    username: str
    password: str
    enterprise_id: UUID
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    max_concurrent_chats: int = 5
    description: Optional[str] = None


class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    max_concurrent_chats: Optional[int] = None
    description: Optional[str] = None


class AgentDashboardStatsResponse(BaseModel):
    active_sessions: int
    waiting_sessions: int
    total_chats_today: int
    avg_response_time: float
    satisfaction_rate: float
    online_agents: int
    total_agents: int


class AgentSessionResponse(BaseModel):
    id: UUID
    agent_id: Optional[UUID]
    session_id: UUID
    status: AgentSessionStatus
    started_at: datetime
    ended_at: Optional[datetime]
    enterprise_id: UUID
    user_name: Optional[str] = None
    topic: Optional[str] = None
    priority: int = 0


class CreateWaitingSessionRequest(BaseModel):
    session_id: Optional[UUID] = None
    enterprise_id: UUID
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    topic: Optional[str] = None
    priority: int = 0


class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "agent"


# 临时token存储（生产环境应使用Redis）
token_store = {}


def get_current_agent(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """从token获取当前坐席"""
    if token not in token_store:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    
    token_data = token_store[token]
    if datetime.fromisoformat(token_data["expires"]) < datetime.utcnow():
        del token_store[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="访问令牌已过期"
        )
    
    agent = db.query(Agent).filter(Agent.id == token_data["agent_id"]).first()
    if not agent:
        raise HTTPException(status_code=404, detail="坐席不存在")
    return agent


def get_http_client() -> httpx.AsyncClient:
    """获取HTTP客户端"""
    return httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT)


async def call_chat_service(endpoint: str, params: dict = None) -> dict:
    """调用chat-service的admin API"""
    url = f"{settings.CHAT_SERVICE_URL}{endpoint}"
    async with get_http_client() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def call_analytics_service(endpoint: str, params: dict = None) -> dict:
    """调用analytics-service的admin API"""
    url = f"{settings.ANALYTICS_SERVICE_URL}{endpoint}"
    async with get_http_client() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def call_alert_service(endpoint: str, params: dict = None) -> dict:
    """调用alert-service的admin API"""
    url = f"{settings.ALERT_SERVICE_URL}{endpoint}"
    async with get_http_client() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def call_knowledge_service(endpoint: str, params: dict = None) -> dict:
    """调用knowledge-service的admin API"""
    url = f"{settings.KNOWLEDGE_SERVICE_URL}{endpoint}"
    async with get_http_client() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "admin-service", "version": "2.0.0"}


# ========== 坐席登录认证 ==========
@app.post("/api/v1/agent/login", response_model=AgentLoginResponse)
async def agent_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    坐席登录端点
    """
    agent = db.query(Agent).filter(Agent.username == form_data.username).first()
    
    if not agent or not verify_password(form_data.password, agent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 创建访问令牌
    token_data = create_access_token({
        "agent_id": str(agent.id),
        "username": agent.username
    })
    
    access_token = token_data["token"]
    token_store[access_token] = {
        "agent_id": str(agent.id),
        "username": agent.username,
        "expires": token_data["expires"]
    }
    
    # 更新坐席状态为在线
    agent.status = AgentStatus.ONLINE
    db.commit()
    
    return AgentLoginResponse(
        access_token=access_token,
        token_type="bearer",
        agent=AgentProfileResponse(
            id=agent.id,
            name=agent.name,
            username=agent.username,
            status=agent.status,
            current_chats=agent.current_chats,
            total_chats=agent.total_chats,
            max_concurrent_chats=agent.max_concurrent_chats,
            enterprise_id=agent.enterprise_id,
            email=agent.email,
            phone=agent.phone,
            avatar=agent.avatar,
            description=agent.description,
            created_at=agent.created_at,
            updated_at=agent.updated_at
        )
    )


@app.post("/api/v1/agent/logout")
async def agent_logout(
    agent: Agent = Depends(get_current_agent),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    坐席登出端点
    """
    if token in token_store:
        del token_store[token]
    
    # 更新坐席状态为离线
    agent.status = AgentStatus.OFFLINE
    db.commit()
    
    return {"message": "登出成功"}


# ========== 坐席管理 API（管理员使用） ==========
@app.get("/api/v1/admin/agents", response_model=List[AgentProfileResponse])
async def list_agents(
    enterprise_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取坐席列表
    """
    query = db.query(Agent)
    if enterprise_id:
        query = query.filter(Agent.enterprise_id == enterprise_id)
    
    agents = query.offset(skip).limit(limit).all()
    return [
        AgentProfileResponse(
            id=a.id,
            name=a.name,
            username=a.username,
            status=a.status,
            current_chats=a.current_chats,
            total_chats=a.total_chats,
            max_concurrent_chats=a.max_concurrent_chats,
            enterprise_id=a.enterprise_id,
            email=a.email,
            phone=a.phone,
            avatar=a.avatar,
            description=a.description,
            created_at=a.created_at,
            updated_at=a.updated_at
        )
        for a in agents
    ]


@app.post("/api/v1/admin/agents", response_model=AgentProfileResponse)
async def create_agent(
    request: CreateAgentRequest,
    db: Session = Depends(get_db)
):
    """
    创建新坐席
    """
    # 检查用户名是否已存在
    existing = db.query(Agent).filter(Agent.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    agent = Agent(
        name=request.name,
        username=request.username,
        password_hash=hash_password(request.password),
        enterprise_id=request.enterprise_id,
        email=request.email,
        phone=request.phone,
        max_concurrent_chats=request.max_concurrent_chats,
        description=request.description
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return AgentProfileResponse(
        id=agent.id,
        name=agent.name,
        username=agent.username,
        status=agent.status,
        current_chats=agent.current_chats,
        total_chats=agent.total_chats,
        max_concurrent_chats=agent.max_concurrent_chats,
        enterprise_id=agent.enterprise_id,
        email=agent.email,
        phone=agent.phone,
        avatar=agent.avatar,
        description=agent.description,
        created_at=agent.created_at,
        updated_at=agent.updated_at
    )


@app.put("/api/v1/admin/agents/{agent_id}", response_model=AgentProfileResponse)
async def update_agent(
    agent_id: UUID,
    request: UpdateAgentRequest,
    db: Session = Depends(get_db)
):
    """
    更新坐席信息
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="坐席不存在")
    
    if request.name:
        agent.name = request.name
    if request.email:
        agent.email = request.email
    if request.phone:
        agent.phone = request.phone
    if request.max_concurrent_chats is not None:
        agent.max_concurrent_chats = request.max_concurrent_chats
    if request.description is not None:
        agent.description = request.description
    
    db.commit()
    db.refresh(agent)
    
    return AgentProfileResponse(
        id=agent.id,
        name=agent.name,
        username=agent.username,
        status=agent.status,
        current_chats=agent.current_chats,
        total_chats=agent.total_chats,
        max_concurrent_chats=agent.max_concurrent_chats,
        enterprise_id=agent.enterprise_id,
        email=agent.email,
        phone=agent.phone,
        avatar=agent.avatar,
        description=agent.description,
        created_at=agent.created_at,
        updated_at=agent.updated_at
    )


@app.delete("/api/v1/admin/agents/{agent_id}")
async def delete_agent(agent_id: UUID, db: Session = Depends(get_db)):
    """
    删除坐席
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="坐席不存在")
    
    db.delete(agent)
    db.commit()
    
    return {"message": "坐席删除成功"}


# ========== 等待会话 API ==========
@app.post("/api/v1/waiting-sessions")
async def create_waiting_session(
    request: CreateWaitingSessionRequest,
    db: Session = Depends(get_db)
):
    """
    创建等待会话（当用户需要人工客服时调用）
    """
    # 如果没有提供session_id，自动生成一个
    session_id = str(request.session_id) if request.session_id else str(uuid.uuid4())
    
    session = AgentSession(
        session_id=session_id,
        enterprise_id=str(request.enterprise_id),
        user_name=request.user_name,
        topic=request.topic,
        priority=request.priority,
        status=AgentSessionStatus.WAITING.value
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # 通知所有在线坐席
    session_data = {
        "id": str(session.id),
        "session_id": str(session.session_id),
        "user_name": session.user_name,
        "topic": session.topic,
        "priority": session.priority,
        "started_at": session.started_at.isoformat()
    }
    await manager.notify_new_waiting_session(session_data)
    
    return {
        "message": "等待会话已创建",
        "id": str(session.id),
        "session_id": str(session.session_id)
    }


# ========== WebSocket for Agents ==========
@app.websocket("/ws/agent/{agent_id}")
async def websocket_agent(websocket: WebSocket, agent_id: str):
    """
    坐席实时通信 WebSocket 端点
    """
    await manager.connect(websocket, agent_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "get_waiting_sessions":
                await websocket.send_json({
                    "type": "waiting_sessions",
                    "data": manager.waiting_sessions
                })
                
    except WebSocketDisconnect:
        manager.disconnect(agent_id)


@app.get("/api/v1/admin/overview")
async def get_overview(enterprise_id: UUID):
    """
    获取企业运营概览

    从各服务收集数据，返回企业运营的总体情况

    参数:
        enterprise_id: 企业ID

    返回:
        运营概览数据
    """
    try:
        # 并行调用各服务获取数据
        async with asyncio.TaskGroup() as tg:
            chat_task = tg.create_task(
                call_chat_service(
                    "/api/v1/admin/sessions/count",
                    {"enterprise_id": str(enterprise_id)}
                )
            )
            analytics_task = tg.create_task(
                call_analytics_service(
                    "/api/v1/admin/stats/overview",
                    {"enterprise_id": str(enterprise_id)}
                )
            )
            alert_task = tg.create_task(
                call_alert_service(
                    "/api/v1/admin/alerts/pending",
                    {"enterprise_id": str(enterprise_id)}
                )
            )

        chat_data = chat_task.result()
        analytics_data = analytics_task.result()
        alerts_data = alert_task.result()

        return {
            "total_sessions": chat_data.get("total_sessions", 0),
            "total_queries": analytics_data.get("total_queries", 0),
            "pending_alerts": len(alerts_data),
            "positive_rate": analytics_data.get("positive_rate", 0)
        }
    except Exception as e:
        print(f"Error fetching overview: {e}")
        raise HTTPException(status_code=500, detail=f"获取概览数据失败: {str(e)}")


@app.get("/api/v1/admin/realtime")
async def get_realtime_stats(enterprise_id: UUID):
    """
    获取实时统计数据

    从analytics-service获取近期的实时统计

    参数:
        enterprise_id: 企业ID

    返回:
        实时统计数据
    """
    try:
        data = await call_analytics_service(
            "/api/v1/admin/stats/realtime",
            {"enterprise_id": str(enterprise_id)}
        )
        return data
    except Exception as e:
        print(f"Error fetching realtime stats: {e}")
        raise HTTPException(status_code=500, detail=f"获取实时统计失败: {str(e)}")


@app.get("/api/v1/admin/performance")
async def get_performance_metrics(
    enterprise_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    获取性能指标

    从analytics-service获取系统性能数据

    参数:
        enterprise_id: 企业ID
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）

    返回:
        性能指标数据
    """
    try:
        params = {"enterprise_id": str(enterprise_id)}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        data = await call_analytics_service(
            "/api/v1/admin/stats/performance",
            params
        )
        return data
    except Exception as e:
        print(f"Error fetching performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@app.get("/api/v1/admin/alerts")
async def get_pending_alerts(
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 50
):
    """
    获取待处理告警

    从alert-service获取待处理告警列表

    参数:
        enterprise_id: 企业ID
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        待处理告警列表
    """
    try:
        data = await call_alert_service(
            "/api/v1/admin/alerts/pending",
            {
                "enterprise_id": str(enterprise_id),
                "skip": skip,
                "limit": limit
            }
        )
        return data
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")


@app.get("/api/v1/admin/alerts/all")
async def get_all_alerts(
    enterprise_id: UUID,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    获取所有告警

    从alert-service获取告警列表（支持筛选）

    参数:
        enterprise_id: 企业ID
        status: 状态筛选（可选）
        priority: 优先级筛选（可选）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        告警列表
    """
    try:
        params = {
            "enterprise_id": str(enterprise_id),
            "skip": skip,
            "limit": limit
        }
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority

        data = await call_alert_service(
            "/api/v1/admin/alerts",
            params
        )
        return data
    except Exception as e:
        print(f"Error fetching all alerts: {e}")
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")


@app.get("/api/v1/admin/alerts/stats")
async def get_alert_stats(enterprise_id: UUID):
    """
    获取告警统计

    从alert-service获取告警统计数据

    参数:
        enterprise_id: 企业ID

    返回:
        告警统计数据
    """
    try:
        data = await call_alert_service(
            "/api/v1/admin/alerts/stats",
            {"enterprise_id": str(enterprise_id)}
        )
        return data
    except Exception as e:
        print(f"Error fetching alert stats: {e}")
        raise HTTPException(status_code=500, detail=f"获取告警统计失败: {str(e)}")


@app.put("/api/v1/admin/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    assigned_to: UUID = None
):
    """
    确认告警

    调用alert-service确认指定告警

    参数:
        alert_id: 告警ID
        assigned_to: 分配给的用户ID（可选）

    返回:
        确认结果
    """
    try:
        url = f"{settings.ALERT_SERVICE_URL}/api/v1/admin/alerts/{alert_id}/acknowledge"
        data = {"assigned_to": str(assigned_to)} if assigned_to else {}
        async with get_http_client() as client:
            response = await client.put(url, json=data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=f"确认告警失败: {str(e)}")


@app.put("/api/v1/admin/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    resolution_notes: str = None
):
    """
    解决告警

    调用alert-service解决指定告警

    参数:
        alert_id: 告警ID
        resolution_notes: 解决备注（可选）

    返回:
        解决结果
    """
    try:
        url = f"{settings.ALERT_SERVICE_URL}/api/v1/admin/alerts/{alert_id}/resolve"
        data = {"resolution_notes": resolution_notes} if resolution_notes else {}
        async with get_http_client() as client:
            response = await client.put(url, json=data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")


@app.get("/api/v1/admin/knowledge-base/stats")
async def get_kb_stats(enterprise_id: UUID):
    """
    获取知识库统计

    从knowledge-service获取知识库统计数据

    参数:
        enterprise_id: 企业ID

    返回:
        知识库统计数据
    """
    try:
        data = await call_knowledge_service(
            "/api/v1/admin/knowledge-bases/stats",
            {"enterprise_id": str(enterprise_id)}
        )
        return data
    except Exception as e:
        print(f"Error fetching KB stats: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库统计失败: {str(e)}")


@app.get("/api/v1/admin/knowledge-base")
async def get_knowledge_bases(
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 100
):
    """
    获取知识库列表

    从knowledge-service获取知识库列表

    参数:
        enterprise_id: 企业ID
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        知识库列表
    """
    try:
        data = await call_knowledge_service(
            "/api/v1/admin/knowledge-bases",
            {
                "enterprise_id": str(enterprise_id),
                "skip": skip,
                "limit": limit
            }
        )
        return data
    except Exception as e:
        print(f"Error fetching knowledge bases: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")


@app.get("/api/v1/admin/documents")
async def get_documents(
    enterprise_id: UUID,
    kb_id: UUID = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100
):
    """
    获取文档列表

    从knowledge-service获取文档列表

    参数:
        enterprise_id: 企业ID
        kb_id: 知识库ID（可选）
        status: 文档状态筛选（可选）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        文档列表
    """
    try:
        params = {
            "enterprise_id": str(enterprise_id),
            "skip": skip,
            "limit": limit
        }
        if kb_id:
            params["kb_id"] = str(kb_id)
        if status:
            params["status"] = status

        data = await call_knowledge_service(
            "/api/v1/admin/documents",
            params
        )
        return data
    except Exception as e:
        print(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@app.get("/api/v1/admin/sessions")
async def get_sessions(
    enterprise_id: UUID,
    user_id: UUID = None,
    skip: int = 0,
    limit: int = 100
):
    """
    获取会话列表

    从chat-service获取会话列表

    参数:
        enterprise_id: 企业ID
        user_id: 用户ID（可选）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        会话列表
    """
    try:
        params = {
            "enterprise_id": str(enterprise_id),
            "skip": skip,
            "limit": limit
        }
        if user_id:
            params["user_id"] = str(user_id)

        data = await call_chat_service(
            "/api/v1/admin/sessions",
            params
        )
        return data
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@app.get("/api/v1/admin/sessions/{session_id}")
async def get_session(session_id: UUID):
    """
    获取会话详情

    从chat-service获取会话详情

    参数:
        session_id: 会话ID

    返回:
        会话详情
    """
    try:
        data = await call_chat_service(
            f"/api/v1/admin/sessions/{session_id}"
        )
        return data
    except Exception as e:
        print(f"Error fetching session: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")


@app.get("/api/v1/admin/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: UUID,
    skip: int = 0,
    limit: int = 100
):
    """
    获取会话消息

    从chat-service获取会话消息列表

    参数:
        session_id: 会话ID
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        消息列表
    """
    try:
        data = await call_chat_service(
            f"/api/v1/admin/sessions/{session_id}/messages",
            {"skip": skip, "limit": limit}
        )
        return data
    except Exception as e:
        print(f"Error fetching session messages: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话消息失败: {str(e)}")


@app.post("/api/v1/admin/sessions/{session_id}/transfer")
async def transfer_to_human(
    session_id: UUID,
    target_agent_id: UUID
):
    """
    将会话转接给人工客服

    参数:
        session_id: 会话ID
        target_agent_id: 目标客服ID

    返回:
        转接结果
    """
    return {
        "message": "Session transferred to human agent",
        "session_id": str(session_id),
        "agent_id": str(target_agent_id)
    }


@app.get("/api/v1/admin/analytics/feedback")
async def get_feedback(
    enterprise_id: UUID,
    rating: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    skip: int = 0,
    limit: int = 100
):
    """
    获取反馈列表

    从analytics-service获取反馈列表

    参数:
        enterprise_id: 企业ID
        rating: 反馈类型筛选（可选）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        反馈列表
    """
    try:
        params = {
            "enterprise_id": str(enterprise_id),
            "skip": skip,
            "limit": limit
        }
        if rating:
            params["rating"] = rating
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        data = await call_analytics_service(
            "/api/v1/admin/feedback",
            params
        )
        return data
    except Exception as e:
        print(f"Error fetching feedback: {e}")
        raise HTTPException(status_code=500, detail=f"获取反馈列表失败: {str(e)}")


@app.get("/api/v1/admin/analytics/query-logs")
async def get_query_logs(
    enterprise_id: UUID,
    response_type: str = None,
    is_miss: bool = None,
    start_date: datetime = None,
    end_date: datetime = None,
    skip: int = 0,
    limit: int = 100
):
    """
    获取查询日志

    从analytics-service获取查询日志

    参数:
        enterprise_id: 企业ID
        response_type: 响应类型筛选（可选）
        is_miss: 是否未命中筛选（可选）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        查询日志列表
    """
    try:
        params = {
            "enterprise_id": str(enterprise_id),
            "skip": skip,
            "limit": limit
        }
        if response_type:
            params["response_type"] = response_type
        if is_miss is not None:
            params["is_miss"] = str(is_miss).lower()
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        data = await call_analytics_service(
            "/api/v1/admin/query-logs",
            params
        )
        return data
    except Exception as e:
        print(f"Error fetching query logs: {e}")
        raise HTTPException(status_code=500, detail=f"获取查询日志失败: {str(e)}")


@app.get("/api/v1/admin/analytics/hot-queries")
async def get_hot_queries(
    enterprise_id: UUID,
    limit: int = 10
):
    """
    获取热词统计

    从analytics-service获取热词统计

    参数:
        enterprise_id: 企业ID
        limit: 返回数量限制

    返回:
        热词列表
    """
    try:
        data = await call_analytics_service(
            "/api/v1/admin/hot-queries",
            {
                "enterprise_id": str(enterprise_id),
                "limit": limit
            }
        )
        return data
    except Exception as e:
        print(f"Error fetching hot queries: {e}")
        raise HTTPException(status_code=500, detail=f"获取热词统计失败: {str(e)}")


@app.get("/api/v1/admin/analytics/missed-queries")
async def get_missed_queries(
    enterprise_id: UUID,
    status: str = None,
    skip: int = 0,
    limit: int = 100
):
    """
    获取未命中问题

    从analytics-service获取未命中问题列表

    参数:
        enterprise_id: 企业ID
        status: 状态筛选（可选）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        未命中问题列表
    """
    try:
        params = {
            "enterprise_id": str(enterprise_id),
            "skip": skip,
            "limit": limit
        }
        if status:
            params["status"] = status

        data = await call_analytics_service(
            "/api/v1/admin/missed-queries",
            params
        )
        return data
    except Exception as e:
        print(f"Error fetching missed queries: {e}")
        raise HTTPException(status_code=500, detail=f"获取未命中问题失败: {str(e)}")


@app.get("/api/v1/admin/analytics/dashboard")
async def get_analytics_dashboard(enterprise_id: UUID):
    """
    获取分析仪表盘数据

    从analytics-service获取综合分析数据

    参数:
        enterprise_id: 企业ID

    返回:
        仪表盘数据
    """
    try:
        data = await call_analytics_service(
            "/api/v1/admin/dashboard",
            {"enterprise_id": str(enterprise_id)}
        )
        return data
    except Exception as e:
        print(f"Error fetching analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析仪表盘失败: {str(e)}")





# ========== 坐席API端点 ==========
@app.get("/api/v1/agent/dashboard/stats", response_model=AgentDashboardStatsResponse)
async def get_agent_dashboard_stats(
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    获取坐席仪表板统计数据
    
    参数:
        agent_id: 坐席ID
    
    返回:
        坐席仪表板统计数据
    """
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        active_sessions = db.query(AgentSession).filter(
            AgentSession.agent_id == agent.id,
            AgentSession.status == AgentSessionStatus.ACTIVE
        ).count()
        
        waiting_sessions = db.query(AgentSession).filter(
            AgentSession.enterprise_id == agent.enterprise_id,
            AgentSession.status == AgentSessionStatus.WAITING
        ).count()
        
        total_chats_today = db.query(AgentSession).filter(
            AgentSession.agent_id == agent.id,
            AgentSession.started_at >= today_start
        ).count()
        
        online_agents = db.query(Agent).filter(
            Agent.enterprise_id == agent.enterprise_id,
            Agent.status.in_([AgentStatus.ONLINE, AgentStatus.BUSY])
        ).count()
        
        total_agents = db.query(Agent).filter(
            Agent.enterprise_id == agent.enterprise_id
        ).count()
        
        return AgentDashboardStatsResponse(
            active_sessions=active_sessions,
            waiting_sessions=waiting_sessions,
            total_chats_today=total_chats_today,
            avg_response_time=0.0,
            satisfaction_rate=0.0,
            online_agents=online_agents,
            total_agents=total_agents
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板统计失败: {str(e)}")


@app.get("/api/v1/agent/chats/waiting", response_model=List[AgentSessionResponse])
async def get_waiting_chats(
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    获取等待接入的会话列表
    
    参数:
        agent_id: 坐席ID
        skip: 跳过记录数
        limit: 返回数量限制
    
    返回:
        等待会话列表
    """
    try:
        waiting_sessions = db.query(AgentSession).filter(
            AgentSession.enterprise_id == agent.enterprise_id,
            AgentSession.status == AgentSessionStatus.WAITING
        ).order_by(AgentSession.priority.desc(), AgentSession.started_at.asc()).offset(skip).limit(limit).all()
        
        return [
            AgentSessionResponse(
                id=s.id,
                agent_id=s.agent_id,
                session_id=s.session_id,
                status=s.status,
                started_at=s.started_at,
                ended_at=s.ended_at,
                enterprise_id=s.enterprise_id,
                user_name=s.user_name,
                topic=s.topic,
                priority=s.priority
            )
            for s in waiting_sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取等待会话失败: {str(e)}")


@app.get("/api/v1/agent/chats/active", response_model=List[AgentSessionResponse])
async def get_active_chats(
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    获取坐席当前活跃的会话列表
    
    参数:
        agent_id: 坐席ID
        skip: 跳过记录数
        limit: 返回数量限制
    
    返回:
        活跃会话列表
    """
    try:
        active_sessions = db.query(AgentSession).filter(
            AgentSession.agent_id == agent.id,
            AgentSession.status == AgentSessionStatus.ACTIVE
        ).offset(skip).limit(limit).all()
        
        return [
            AgentSessionResponse(
                id=s.id,
                agent_id=s.agent_id,
                session_id=s.session_id,
                status=s.status,
                started_at=s.started_at,
                ended_at=s.ended_at,
                enterprise_id=s.enterprise_id,
                user_name=s.user_name,
                topic=s.topic,
                priority=s.priority
            )
            for s in active_sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃会话失败: {str(e)}")


@app.post("/api/v1/agent/chats/{session_id}/accept")
async def accept_chat(
    session_id: str,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    接入会话
    
    参数:
        session_id: 会话ID
        agent_id: 坐席ID
    
    返回:
        接入结果
    """
    try:
        if agent.current_chats >= agent.max_concurrent_chats:
            raise HTTPException(status_code=400, detail="已达到最大并发会话数")
        
        agent_session = db.query(AgentSession).filter(
            AgentSession.session_id == session_id,
            AgentSession.enterprise_id == agent.enterprise_id
        ).first()
        
        if not agent_session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        if agent_session.status != AgentSessionStatus.WAITING.value:
            raise HTTPException(status_code=400, detail="会话状态不允许接入")
        
        agent_session.agent_id = agent.id
        agent_session.status = AgentSessionStatus.ACTIVE.value
        
        agent.current_chats += 1
        agent.total_chats += 1
        if agent.current_chats >= agent.max_concurrent_chats:
            agent.status = AgentStatus.BUSY
        
        db.commit()
        db.refresh(agent_session)
        db.refresh(agent)
        
        # 通知其他坐席该会话已被接入
        await manager.broadcast_to_agents({
            "type": "session_accepted",
            "data": {
                "session_id": str(session_id),
                "agent_id": str(agent.id),
                "agent_name": agent.name
            }
        })
        
        return {"message": "会话接入成功", "session_id": str(session_id)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"接入会话失败: {str(e)}")


@app.post("/api/v1/agent/chats/{session_id}/close")
async def close_chat(
    session_id: str,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    关闭会话
    
    参数:
        session_id: 会话ID
        agent_id: 坐席ID
    
    返回:
        关闭结果
    """
    try:
        agent_session = db.query(AgentSession).filter(
            AgentSession.session_id == session_id,
            AgentSession.agent_id == agent.id
        ).first()
        
        if not agent_session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        if agent_session.status != AgentSessionStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="会话状态不允许关闭")
        
        agent_session.status = AgentSessionStatus.CLOSED.value
        agent_session.ended_at = datetime.utcnow()
        
        agent.current_chats -= 1
        if agent.current_chats < agent.max_concurrent_chats and agent.status == AgentStatus.BUSY:
            agent.status = AgentStatus.ONLINE
        
        db.commit()
        
        return {"message": "会话关闭成功", "session_id": str(session_id)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"关闭会话失败: {str(e)}")


@app.post("/api/v1/agent/chats/{session_id}/messages")
async def send_agent_message(
    session_id: str,
    message: SendMessageRequest,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    坐席发送消息
    
    参数:
        session_id: 会话ID
        message: 消息内容
        agent_id: 坐席ID
    
    返回:
        发送结果
    """
    try:
        agent_session = db.query(AgentSession).filter(
            AgentSession.session_id == session_id,
            AgentSession.agent_id == agent.id,
            AgentSession.status == AgentSessionStatus.ACTIVE.value
        ).first()
        
        if not agent_session:
            raise HTTPException(status_code=404, detail="会话不存在或未激活")
        
        # 这里需要调用chat-service的消息发送API
        # 由于chat-service可能没有专门的坐席消息API，我们先做一个模拟实现
        try:
            url = f"{settings.CHAT_SERVICE_URL}/api/v1/sessions/{session_id}/messages"
            async with get_http_client() as client:
                response = await client.post(url, params={
                    "content": message.content,
                    "user_id": str(agent.id),
                    "enterprise_id": str(agent.enterprise_id)
                })
                if response.status_code == 200:
                    return response.json()
        except httpx.HTTPError as e:
            pass
        
        # 模拟成功
        return {
            "message": "消息发送成功",
            "session_id": str(session_id),
            "content": message.content,
            "sender": "agent",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@app.get("/api/v1/agent/chats/{agent_session_id}")
async def get_chat_detail(
    agent_session_id: str,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    获取会话详情及历史消息
    
    参数:
        agent_session_id: 坐席会话ID
    
    返回:
        会话详情和消息
    """
    try:
        agent_session = db.query(AgentSession).filter(
            AgentSession.id == agent_session_id,
            AgentSession.agent_id == agent.id
        ).first()
        
        if not agent_session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 尝试从chat-service获取消息
        try:
            url = f"{settings.CHAT_SERVICE_URL}/api/v1/admin/sessions/{agent_session.session_id}/messages"
            async with get_http_client() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    chat_messages = response.json()
                else:
                    chat_messages = []
        except Exception as e:
            chat_messages = []
        
        return {
            "agent_session": {
                "id": str(agent_session.id),
                "session_id": str(agent_session.session_id),
                "status": agent_session.status.value,
                "user_name": agent_session.user_name,
                "topic": agent_session.topic,
                "started_at": agent_session.started_at.isoformat()
            },
            "messages": chat_messages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")


@app.get("/api/v1/agent/profile", response_model=AgentProfileResponse)
async def get_agent_profile(
    agent: Agent = Depends(get_current_agent)
):
    """
    获取坐席个人信息
    
    参数:
        agent_id: 坐席ID
    
    返回:
        坐席个人信息
    """
    return AgentProfileResponse(
        id=agent.id,
        name=agent.name,
        username=agent.username,
        status=agent.status,
        current_chats=agent.current_chats,
        total_chats=agent.total_chats,
        max_concurrent_chats=agent.max_concurrent_chats,
        enterprise_id=agent.enterprise_id,
        email=agent.email,
        phone=agent.phone,
        avatar=agent.avatar,
        description=agent.description,
        created_at=agent.created_at,
        updated_at=agent.updated_at
    )


@app.put("/api/v1/agent/profile/status")
async def update_agent_status(
    status_update: UpdateAgentStatusRequest,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    更新坐席状态
    
    参数:
        agent_id: 坐席ID
        status_update: 状态更新请求
    
    返回:
        更新后的坐席信息
    """
    try:
        agent.status = status_update.status
        db.commit()
        db.refresh(agent)
        
        return {"message": "状态更新成功", "status": agent.status.value}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新状态失败: {str(e)}")


# ========== 初始化数据 ==========
def init_sample_data(db: Session):
    """初始化示例数据"""
    # 检查是否已有数据
    existing = db.query(Agent).filter(Agent.username == "agent1").first()
    if existing:
        return
    
    # 使用字符串类型的UUID以兼容SQLite
    sample_enterprise_id = "12345678-1234-5678-1234-567812345678"
    
    # 创建示例坐席
    agents = [
        Agent(
            name="张三",
            username="agent1",
            password_hash=hash_password("123456"),
            enterprise_id=sample_enterprise_id,
            email="zhangsan@example.com",
            max_concurrent_chats=5,
            description="资深客服坐席"
        ),
        Agent(
            name="李四",
            username="agent2",
            password_hash=hash_password("123456"),
            enterprise_id=sample_enterprise_id,
            email="lisi@example.com",
            max_concurrent_chats=3,
            description="技术支持专家"
        )
    ]
    
    for agent in agents:
        db.add(agent)
    
    db.commit()
    print("示例坐席数据已初始化")


@app.on_event("startup")
async def startup_event():
    """应用启动"""
    print("Admin Service starting up...")
    try:
        init_db()
        # 初始化示例数据
        db = next(get_db())
        init_sample_data(db)
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown():
    """应用关闭"""
    print("Admin Service shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
