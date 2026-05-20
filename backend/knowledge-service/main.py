"""
Knowledge Service - 知识库管理服务
===================================

主要功能：
- 知识库管理：创建、查询、删除知识库
- 文档处理：上传、解析、文本提取
- 向量存储：文本分块、向量化、相似度检索
- FAQ管理：常见问题配置和优先级设置
- 重排序：使用Cross-Encoder优化检索结果

核心技术：
- ChromaDB：向量数据库存储文档嵌入
- Text Chunker：智能文本分块算法
- Embedding：文本向量化（用于语义检索）
- Cross-Encoder Rerank：重排序提升检索精度
"""

# FastAPI核心框架
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
# CORS跨域支持
from fastapi.middleware.cors import CORSMiddleware
# SQLAlchemy ORM
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import tempfile
import os
import json

# 导入配置
from .config import settings
# 导入数据库连接
from .database import get_db, init_db
# 导入Redis客户端
from .redis_client import redis_manager
# 导入数据模型
from .models import KnowledgeBase, Document
# 导入向量存储
from .vector_store import get_vector_store
# 导入文本分块器
from .chunker import TextChunker, extract_text_from_file
# 导入FAQ路由
from .faq_endpoints import router as faq_router


# 创建FastAPI应用
app = FastAPI(
    title="Knowledge Service",
    description="知识库管理服务，支持FAQ和版本控制",
    version="1.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册FAQ路由
app.include_router(faq_router)


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """
    健康检查端点

    用于负载均衡器和容器编排检测服务状态
    """
    return {"status": "healthy", "service": "knowledge-service"}


# ==================== 知识库管理API ====================

@app.post("/api/v1/knowledge-bases")
async def create_knowledge_base(
    name: str,
    enterprise_id: UUID,
    description: str = None,
    db: Session = Depends(get_db)
):
    """
    创建知识库

    为企业创建一个新的知识库，用于存储和管理相关文档

    参数:
        name: 知识库名称
        enterprise_id: 企业ID
        description: 知识库描述（可选）
        db: 数据库会话

    返回:
        创建的知识库信息
    """
    kb = KnowledgeBase(
        enterprise_id=enterprise_id,
        name=name,
        description=description
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)

    return {
        "id": str(kb.id),
        "name": kb.name,
        "description": kb.description,
        "created_at": kb.created_at.isoformat()
    }


@app.get("/api/v1/knowledge-bases")
async def list_knowledge_bases(
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    列出知识库

    获取企业的所有知识库列表

    参数:
        enterprise_id: 企业ID
        skip: 跳过记录数（分页）
        limit: 返回数量限制
        db: 数据库会话

    返回:
        知识库列表
    """
    kbs = db.query(KnowledgeBase).filter(
        KnowledgeBase.enterprise_id == enterprise_id
    ).offset(skip).limit(limit).all()

    # 转换为字典列表返回
    return [
        {
            "id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count,
            "is_active": kb.is_active,
            "created_at": kb.created_at.isoformat()
        }
        for kb in kbs
    ]


@app.get("/api/v1/knowledge-bases/{kb_id}")
async def get_knowledge_base(kb_id: UUID, db: Session = Depends(get_db)):
    """
    获取知识库详情

    根据知识库ID获取详细信息

    参数:
        kb_id: 知识库ID
        db: 数据库会话

    返回:
        知识库详细信息
    """
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    return {
        "id": str(kb.id),
        "name": kb.name,
        "description": kb.description,
        "document_count": kb.document_count,
        "chunk_count": kb.chunk_count,
        "is_active": kb.is_active,
        "created_at": kb.created_at.isoformat()
    }


@app.delete("/api/v1/knowledge-bases/{kb_id}")
async def delete_knowledge_base(
    kb_id: UUID,
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """
    删除知识库

    删除指定的知识库，同时删除所有关联的向量数据

    参数:
        kb_id: 知识库ID
        enterprise_id: 企业ID（用于验证权限）
        db: 数据库会话
    """
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.enterprise_id == enterprise_id
    ).first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # 删除向量数据库中的相关数据
    try:
        vector_store = get_vector_store()
        vector_store.delete_chunks(str(enterprise_id), str(kb_id))
    except Exception as e:
        print(f"Warning: Failed to delete from vector store: {e}")

    # 删除数据库记录
    db.delete(kb)
    db.commit()

    return {"message": "Knowledge base deleted successfully"}


# ==================== 文档处理 ====================

async def process_document_background(
    document_id: UUID,
    enterprise_id: UUID,
    knowledge_base_id: UUID,
    file_path: str
):
    """
    后台文档处理任务

    异步处理上传的文档，包括：
    1. 文本提取：从文件提取文本内容
    2. 文本分块：将长文本分割成小块
    3. 向量化存储：将文本块存储到向量数据库

    参数:
        document_id: 文档ID
        enterprise_id: 企业ID
        knowledge_base_id: 知识库ID
        file_path: 临时文件路径
    """
    try:
        from .database import get_db_context
        with get_db_context() as db:
            # 第一步：从文件提取文本
            text = extract_text_from_file(file_path)

            # 第二步：文本分块
            chunker = TextChunker()
            chunks = chunker.chunk_text(text, {
                "document_id": str(document_id)
            })

            # 第三步：存储到向量数据库
            vector_store = get_vector_store()
            vector_store.add_chunks(
                str(enterprise_id),
                str(knowledge_base_id),
                chunks
            )

            # 第四步：更新文档状态
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "ready"
                doc.chunk_count = len(chunks)

                # 更新知识库的块计数
                kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
                if kb:
                    kb.chunk_count += len(chunks)

            # 第五步：清理临时文件
            if os.path.exists(file_path):
                os.unlink(file_path)

    except Exception as e:
        print(f"Error processing document: {e}")
        try:
            from .database import get_db_context
            with get_db_context() as db:
                doc = db.query(Document).filter(Document.id == document_id).first()
                if doc:
                    doc.status = "error"
                    doc.error_message = str(e)
        except:
            pass


@app.post("/api/v1/knowledge-bases/{kb_id}/documents")
async def upload_document(
    kb_id: UUID,
    enterprise_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    上传文档到知识库

    接收用户上传的文件，保存到临时目录，
    然后后台异步处理：文本提取、分块、向量化

    参数:
        kb_id: 知识库ID
        enterprise_id: 企业ID
        file: 上传的文件
        background_tasks: 后台任务管理器
        db: 数据库会话

    返回:
        文档上传结果，包含文档ID和状态
    """
    # 验证知识库存在且属于该企业
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.enterprise_id == enterprise_id
    ).first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # 保存上传的文件到临时目录
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # 创建文档记录
    doc = Document(
        knowledge_base_id=kb_id,
        filename=file.filename,
        file_path=tmp_path,
        file_size=len(content),
        file_type=file.filename.split(".")[-1] if "." in file.filename else "unknown",
        status="processing"
    )
    db.add(doc)
    kb.document_count += 1  # 更新知识库文档计数
    db.commit()
    db.refresh(doc)

    # 添加后台处理任务
    background_tasks.add_task(
        process_document_background,
        doc.id,
        enterprise_id,
        kb_id,
        tmp_path
    )

    return {
        "document_id": str(doc.id),
        "filename": doc.filename,
        "status": "processing",
        "message": "Document uploaded and processing"
    }


@app.get("/api/v1/knowledge-bases/{kb_id}/documents")
async def list_documents(
    kb_id: UUID,
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    列出知识库中的文档

    获取指定知识库下的所有文档列表

    参数:
        kb_id: 知识库ID
        enterprise_id: 企业ID
        skip: 跳过记录数
        limit: 返回数量限制
        db: 数据库会话

    返回:
        文档列表
    """
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.enterprise_id == enterprise_id
    ).first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    docs = db.query(Document).filter(
        Document.knowledge_base_id == kb_id
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": str(doc.id),
            "filename": doc.filename,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "created_at": doc.created_at.isoformat()
        }
        for doc in docs
    ]


@app.delete("/api/v1/documents/{doc_id}")
async def delete_document(
    doc_id: UUID,
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """
    删除文档

    从知识库中删除指定的文档，
    同时删除向量数据库中的相关数据和磁盘上的文件

    参数:
        doc_id: 文档ID
        enterprise_id: 企业ID
        db: 数据库会话
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 删除向量数据
    try:
        vector_store = get_vector_store()
        vector_store.delete_document(str(enterprise_id), str(doc_id))
    except Exception as e:
        print(f"Warning: Failed to delete from vector store: {e}")

    # 更新知识库统计
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == doc.knowledge_base_id).first()
    if kb:
        kb.document_count -= 1
        kb.chunk_count -= doc.chunk_count

    # 删除物理文件
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.unlink(doc.file_path)
        except:
            pass

    # 删除数据库记录
    db.delete(doc)
    db.commit()

    return {"message": "Document deleted successfully"}


# ==================== 管理员API端点 ====================

@app.get("/api/v1/admin/knowledge-bases")
async def admin_list_knowledge_bases(
    enterprise_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    管理员列出知识库

    供admin-service调用，返回指定企业的所有知识库

    参数:
        enterprise_id: 企业ID
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        知识库列表
    """
    kbs = db.query(KnowledgeBase).filter(
        KnowledgeBase.enterprise_id == enterprise_id
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count,
            "is_active": kb.is_active,
            "metadata": kb.metadata_,
            "created_at": kb.created_at.isoformat(),
            "updated_at": kb.updated_at.isoformat()
        }
        for kb in kbs
    ]


@app.get("/api/v1/admin/knowledge-bases/{kb_id}")
async def admin_get_knowledge_base(
    kb_id: UUID,
    db: Session = Depends(get_db)
):
    """
    管理员获取知识库详情

    供admin-service调用，返回指定知识库的详细信息

    参数:
        kb_id: 知识库ID

    返回:
        知识库详情
    """
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    return {
        "id": str(kb.id),
        "enterprise_id": str(kb.enterprise_id),
        "name": kb.name,
        "description": kb.description,
        "document_count": kb.document_count,
        "chunk_count": kb.chunk_count,
        "is_active": kb.is_active,
        "metadata": kb.metadata_,
        "created_at": kb.created_at.isoformat(),
        "updated_at": kb.updated_at.isoformat()
    }


@app.get("/api/v1/admin/knowledge-bases/stats")
async def admin_get_kb_stats(
    enterprise_id: UUID,
    db: Session = Depends(get_db)
):
    """
    管理员获取知识库统计

    供admin-service调用，返回指定企业的知识库统计数据

    参数:
        enterprise_id: 企业ID

    返回:
        知识库统计数据
    """
    kbs = db.query(KnowledgeBase).filter(
        KnowledgeBase.enterprise_id == enterprise_id
    ).all()

    total_docs = sum(kb.document_count for kb in kbs)
    total_chunks = sum(kb.chunk_count for kb in kbs)

    return {
        "knowledge_base_count": len(kbs),
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "knowledge_bases": [
            {
                "id": str(kb.id),
                "name": kb.name,
                "document_count": kb.document_count,
                "chunk_count": kb.chunk_count,
                "is_active": kb.is_active
            }
            for kb in kbs
        ]
    }


@app.get("/api/v1/admin/documents")
async def admin_list_documents(
    enterprise_id: UUID,
    kb_id: UUID = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    管理员列出文档

    供admin-service调用，返回指定企业的所有文档

    参数:
        enterprise_id: 企业ID
        kb_id: 知识库ID（可选）
        status: 文档状态筛选（可选）
        skip: 跳过记录数
        limit: 返回数量限制

    返回:
        文档列表
    """
    query = db.query(Document).join(KnowledgeBase).filter(
        KnowledgeBase.enterprise_id == enterprise_id
    )

    if kb_id:
        query = query.filter(Document.knowledge_base_id == kb_id)
    if status:
        query = query.filter(Document.status == status)

    docs = query.offset(skip).limit(limit).all()

    return [
        {
            "id": str(doc.id),
            "knowledge_base_id": str(doc.knowledge_base_id),
            "filename": doc.filename,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "error_message": doc.error_message,
            "metadata": doc.metadata_,
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat()
        }
        for doc in docs
    ]


@app.get("/api/v1/admin/documents/{doc_id}")
async def admin_get_document(
    doc_id: UUID,
    db: Session = Depends(get_db)
):
    """
    管理员获取文档详情

    供admin-service调用，返回指定文档的详细信息

    参数:
        doc_id: 文档ID

    返回:
        文档详情
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(doc.id),
        "knowledge_base_id": str(doc.knowledge_base_id),
        "filename": doc.filename,
        "file_path": doc.file_path,
        "file_size": doc.file_size,
        "file_type": doc.file_type,
        "file_hash": doc.file_hash,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "error_message": doc.error_message,
        "metadata": doc.metadata_,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat()
    }


# ==================== 向量检索API ====================

@app.post("/api/v1/retrieve")
async def retrieve_chunks(
    enterprise_id: UUID,
    query: str,
    knowledge_base_ids: Optional[List[UUID]] = None,
    top_k: int = 5,
    enable_rerank: bool = True,
    use_cross_encoder: bool = True
):
    """
    向量检索

    根据查询文本，从知识库中检索最相关的文档块

    检索流程：
    1. 向量相似度搜索：使用Embedding找到相似的文档块
    2. 重排序（如启用）：使用Cross-Encoder优化排序结果
    3. 返回最相关的top_k个结果

    参数:
        enterprise_id: 企业ID
        query: 查询文本
        knowledge_base_ids: 指定的知识库ID列表（可选）
        top_k: 返回结果数量
        enable_rerank: 是否启用重排序
        use_cross_encoder: 是否使用Cross-Encoder

    返回:
        相关文档块列表
    """
    try:
        vector_store = get_vector_store()

        # 转换为字符串列表
        kb_ids = [str(kb_id) for kb_id in knowledge_base_ids] if knowledge_base_ids else None

        # 初步检索，取更多结果用于重排序
        chunks = vector_store.similarity_search(
            str(enterprise_id),
            query,
            kb_ids,
            top_k * 3 if enable_rerank else top_k
        )

        # 重排序优化结果
        if enable_rerank and len(chunks) > 0:
            try:
                from .rerank import get_reranker
                reranker = get_reranker(use_cross_encoder=use_cross_encoder)
                if reranker:
                    chunks = reranker.rerank(query, chunks, top_k)
            except Exception as e:
                print(f"Reranking failed: {e}, using original order")

        return {"chunks": chunks}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 生命周期管理 ====================

@app.on_event("startup")
async def startup():
    """
    应用启动

    初始化数据库和Redis连接
    """
    print("Knowledge Service starting up...")
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
    await redis_manager.connect()


@app.on_event("shutdown")
async def shutdown():
    """
    应用关闭

    清理Redis连接
    """
    print("Knowledge Service shutting down...")
    await redis_manager.disconnect()
