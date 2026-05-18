"""
RAG (Retrieval-Augmented Generation) logic with Hybrid Search
and Citation support.

Hybrid Search Flow:
1. FAQ Matching (PostgreSQL) - keyword/fuzzy match on faq_table
2. RAG Retrieval (ChromaDB) - if FAQ miss, do vector search

Citation Support:
- LLM generates answers with [来源: filename] citations
- Response includes structured sources list
"""
from typing import List, Dict, Any, Optional, Tuple
import httpx
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db_context
from .faq_models import FAQ


class RAGEngine:
    """RAG engine with Hybrid Search and Citation support"""
    
    def __init__(self):
        self.knowledge_service_url = settings.KNOWLEDGE_SERVICE_URL
        self.faq_threshold = 0.85  # High threshold for FAQ matching
        self.rag_threshold = 0.7   # Threshold for RAG chunks
    
    async def retrieve(
        self,
        enterprise_id: str,
        query: str,
        knowledge_base_ids: Optional[List[str]] = None,
        top_k: int = None,
        enable_rerank: bool = True,
        use_cross_encoder: bool = True
    ) -> Dict[str, Any]:
        """
        Hybrid retrieval flow.
        
        Step 1: FAQ Matching (PostgreSQL)
        Step 2: RAG Retrieval (ChromaDB)
        
        Returns:
            {
                "source_type": "faq" | "rag",
                "answer": str,
                "sources": List[Dict],
                "chunks": List[Dict]  # for RAG case
            }
        """
        # Step 1: Try FAQ Matching first
        faq_result = await self._faq_match(enterprise_id, query)
        if faq_result:
            return faq_result
        
        # Step 2: FAQ miss, do RAG retrieval
        rag_result = await self._rag_retrieve(
            enterprise_id,
            query,
            knowledge_base_ids,
            top_k,
            enable_rerank,
            use_cross_encoder
        )
        
        return rag_result
    
    async def _faq_match(
        self,
        enterprise_id: str,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Step 1: FAQ Matching via Knowledge Service API.
        
        Returns:
            {
                "source_type": "faq",
                "answer": str,
                "sources": [{"filename": "FAQ Database", "page": None, "score": 1.0}],
                "is_faq": True
            }
            or None if no match
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.knowledge_service_url}/api/v1/faqs/match",
                    params={
                        "enterprise_id": enterprise_id,
                        "query": query
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("matched"):
                        faq = data.get("faq")
                        return {
                            "source_type": "faq",
                            "answer": faq.get("answer"),
                            "sources": [{
                                "filename": "FAQ Database",
                                "page": None,
                                "score": 1.0,
                                "chunk_number": None
                            }],
                            "is_faq": True,
                            "faq_id": faq.get("id"),
                            "chunks": []
                        }
            
            return None
        except Exception as e:
            print(f"FAQ matching via API error: {e}")
            return None
    
    async def _rag_retrieve(
        self,
        enterprise_id: str,
        query: str,
        knowledge_base_ids: Optional[List[str]] = None,
        top_k: int = None,
        enable_rerank: bool = True,
        use_cross_encoder: bool = True
    ) -> Dict[str, Any]:
        """
        Step 2: RAG Retrieval from knowledge service.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.knowledge_service_url}/api/v1/retrieve",
                    params={
                        "enterprise_id": enterprise_id,
                        "query": query,
                        "top_k": top_k or settings.TOP_K,
                        "enable_rerank": enable_rerank,
                        "use_cross_encoder": use_cross_encoder
                    },
                    json={"knowledge_base_ids": knowledge_base_ids} if knowledge_base_ids else None
                )
                response.raise_for_status()
                data = response.json()
                chunks = data.get("chunks", [])
                
                # Format sources
                sources = self._format_sources(chunks)
                
                return {
                    "source_type": "rag",
                    "answer": None,  # Answer will be generated by LLM
                    "sources": sources,
                    "chunks": chunks,
                    "is_faq": False
                }
        except Exception as e:
            print(f"Failed to retrieve from knowledge service: {e}")
            return {
                "source_type": "rag",
                "answer": None,
                "sources": [],
                "chunks": [],
                "is_faq": False
            }
    
    def _format_sources(self, chunks: List[Dict]) -> List[Dict[str, Any]]:
        """
        Format chunks into structured sources list.
        
        Output format:
        [
            {
                "filename": "product_manual.pdf",
                "page": 15,
                "score": 0.95,
                "chunk_number": 0,
                "content": "..."
            }
        ]
        """
        sources = []
        for i, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "Unknown")
            page = metadata.get("page")
            distance = chunk.get("distance", 0)
            score = 1 - distance
            
            sources.append({
                "filename": filename,
                "page": page,
                "score": round(score, 3),
                "chunk_number": i,
                "content": chunk.get("content", "")[:100] + "..."
            })
        
        return sources
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context with citations"""
        if not chunks:
            return ""
        
        context = "相关上下文：\n\n"
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("filename", "Unknown")
            
            context += f"[来源{i}] 文档：{source}\n"
            
            if chunk.get("metadata", {}).get("page"):
                context += f"页码：{chunk['metadata']['page']}\n"
            
            if "rerank_rank" in chunk:
                context += f"重排序：第{chunk['rerank_rank']}名\n"
                if "combined_score" in chunk:
                    context += f"综合评分：{chunk['combined_score']:.3f}\n"
            
            context += f"内容：{chunk['content']}\n\n"
        
        return context
    
    def generate_prompt(
        self,
        query: str,
        context: str,
        history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate prompt with citation requirements.
        
        System Prompt requires LLM to cite sources in answers.
        """
        prompt = f"""你是一个专业的智能客服助手。请根据提供的上下文信息来回答用户的问题。

重要要求：
1. 所有回答必须基于提供的上下文信息，不能编造信息
2. 回答内容必须引用上下文来源，格式为：[来源: 文档名]
   例如：根据文档，我们的营业时间是周一至周五的9:00-18:00 [来源: 产品手册.pdf]
3. 如果上下文信息不足，请诚实告知用户无法回答该问题
4. 回答要简洁明了，避免冗长

{context}

用户问题：{query}

"""
        
        if history:
            prompt += "对话历史：\n"
            for msg in history[-5:]:
                role = "用户" if msg["role"] == "user" else "助手"
                prompt += f"{role}：{msg['content']}\n"
            prompt += "\n"
        
        prompt += "请给出回答（必须标注引用来源）："
        
        return prompt


_rag_engine = None


def get_rag_engine() -> RAGEngine:
    """Get or create RAG engine singleton"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
