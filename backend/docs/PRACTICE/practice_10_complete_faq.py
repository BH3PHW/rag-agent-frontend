# 练习10: 完整FAQ系统
# 运行前安装: pip install fastapi uvicorn sqlalchemy redis
# 运行: python practice_10_complete_faq.py
# 访问: http://localhost:8080/docs

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import json
from datetime import timedelta
from typing import List, Optional

app = FastAPI(title="练习10 - 完整FAQ系统")

# 数据库配置
DATABASE_URL = "sqlite:///./practice_faq_system.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis配置（可选）
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=1,
        decode_responses=True
    )
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    print("⚠️  Redis不可用，将不使用缓存")

# 数据模型（数据库）
class FAQModel(Base):
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(200), nullable=False, unique=True)
    answer = Column(String(500), nullable=False)
    category = Column(String(50), default="其他")
    views = Column(Integer, default=0)
    active = Column(Boolean, default=True)

# 创建表
Base.metadata.create_all(bind=engine)

# Pydantic模型
class FAQBase(BaseModel):
    question: str
    answer: str
    category: str = "其他"

class FAQCreate(FAQBase):
    pass

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    active: Optional[bool] = None

class FAQResponse(FAQBase):
    id: int
    views: int
    active: bool
    
    class Config:
        orm_mode = True

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 缓存辅助函数
def get_cache_key(question: str) -> str:
    return f"faq:cache:{question}"

# API路由

@app.get("/", tags=["根路径"])
async def root():
    return {
        "message": "欢迎来到完整FAQ系统！",
        "docs": "/docs",
        "endpoints": {
            "GET /faqs": "获取所有FAQ",
            "GET /faqs/{id}": "获取单个FAQ",
            "POST /faqs": "创建FAQ",
            "PUT /faqs/{id}": "更新FAQ",
            "DELETE /faqs/{id}": "删除FAQ",
            "POST /faqs/ask": "提问并获取答案"
        }
    }

@app.get("/faqs", response_model=List[FAQResponse], tags=["FAQ管理"])
async def get_all_faqs(category: Optional[str] = None, active: Optional[bool] = None):
    """获取所有FAQ，可按分类或状态筛选"""
    db = next(get_db())
    query = db.query(FAQModel)
    
    if category:
        query = query.filter(FAQModel.category == category)
    if active is not None:
        query = query.filter(FAQModel.active == active)
    
    return query.all()

@app.get("/faqs/{faq_id}", response_model=FAQResponse, tags=["FAQ管理"])
async def get_faq(faq_id: int):
    """获取单个FAQ详情"""
    db = next(get_db())
    faq = db.query(FAQModel).filter(FAQModel.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ不存在")
    return faq

@app.post("/faqs", response_model=FAQResponse, tags=["FAQ管理"])
async def create_faq(faq: FAQCreate):
    """创建新的FAQ"""
    db = next(get_db())
    
    # 检查重复
    existing = db.query(FAQModel).filter(FAQModel.question == faq.question).first()
    if existing:
        raise HTTPException(status_code=400, detail="该问题已存在")
    
    db_faq = FAQModel(**faq.dict())
    db.add(db_faq)
    db.commit()
    db.refresh(db_faq)
    
    # 清除相关缓存
    if REDIS_AVAILABLE:
        redis_client.delete(get_cache_key(faq.question))
    
    return db_faq

@app.put("/faqs/{faq_id}", response_model=FAQResponse, tags=["FAQ管理"])
async def update_faq(faq_id: int, faq_update: FAQUpdate):
    """更新FAQ"""
    db = next(get_db())
    faq = db.query(FAQModel).filter(FAQModel.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ不存在")
    
    update_data = faq_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(faq, key, value)
    
    db.commit()
    db.refresh(faq)
    
    # 清除缓存
    if REDIS_AVAILABLE:
        redis_client.delete(get_cache_key(faq.question))
    
    return faq

@app.delete("/faqs/{faq_id}", tags=["FAQ管理"])
async def delete_faq(faq_id: int):
    """删除FAQ"""
    db = next(get_db())
    faq = db.query(FAQModel).filter(FAQModel.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ不存在")
    
    question = faq.question
    db.delete(faq)
    db.commit()
    
    # 清除缓存
    if REDIS_AVAILABLE:
        redis_client.delete(get_cache_key(question))
    
    return {"message": "删除成功"}

@app.post("/faqs/ask", tags=["FAQ查询"])
async def ask_faq(question: str):
    """提问并获取答案"""
    db = next(get_db())
    
    # 尝试从缓存获取
    cache_key = get_cache_key(question)
    if REDIS_AVAILABLE:
        cached = redis_client.get(cache_key)
        if cached:
            cached_data = json.loads(cached)
            return {
                "question": question,
                "answer": cached_data["answer"],
                "from_cache": True
            }
    
    # 从数据库查询
    faq = db.query(FAQModel).filter(FAQModel.question == question, FAQModel.active == True).first()
    
    if faq:
        # 增加查看次数
        faq.views += 1
        db.commit()
        
        # 存入缓存
        if REDIS_AVAILABLE:
            cache_data = {"answer": faq.answer, "views": faq.views}
            redis_client.setex(cache_key, timedelta(minutes=10), json.dumps(cache_data))
        
        return {
            "question": question,
            "answer": faq.answer,
            "views": faq.views,
            "from_cache": False
        }
    else:
        # 没有找到，尝试模糊匹配
        similar = db.query(FAQModel).filter(
            FAQModel.question.contains(question[:10]) if len(question) > 10 else FAQModel.question.contains(question)
        ).first()
        
        if similar:
            return {
                "question": question,
                "answer": f"没有找到完全匹配的问题，你是不是想问：{similar.question}？\n答案：{similar.answer}",
                "suggestion": similar.question
            }
        
        return {
            "question": question,
            "answer": "抱歉，没有找到相关答案"
        }

@app.post("/faqs/init-sample", tags=["初始化"])
async def init_sample_data():
    """初始化示例数据"""
    db = next(get_db())
    
    # 清空现有数据
    db.query(FAQModel).delete()
    db.commit()
    
    sample_faqs = [
        FAQModel(question="如何退货？", answer="请在订单页面申请退货，支持7天无理由退货", category="售后"),
        FAQModel(question="配送时间？", answer="通常24小时内发货，3-5天送达", category="配送"),
        FAQModel(question="客服工作时间？", answer="每天9:00-18:00", category="客服"),
        FAQModel(question="如何联系客服？", answer="拨打400-123-4567或在线咨询", category="客服"),
        FAQModel(question="支持哪些支付方式？", answer="支持微信、支付宝、银行卡", category="支付")
    ]
    
    db.add_all(sample_faqs)
    db.commit()
    
    return {"message": "示例数据初始化成功", "count": len(sample_faqs)}

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("📚 练习10: 完整FAQ系统启动中...")
    print("🌐 API文档: http://localhost:8080/docs")
    print("💡 提示: 先调用 /faqs/init-sample 初始化示例数据")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8080)
