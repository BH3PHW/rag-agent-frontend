"""
Multi-level Cache Service for Chat Service

Features:
1. FAQ Cache - Cache frequent FAQ answers
2. Retrieval Cache - Cache vector search results
3. Session Cache - Cache conversation history
4. Smart eviction policies
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
import hashlib

from .redis_client import redis_manager


class CacheService:
    """Multi-level cache service for RAG chat"""
    
    def __init__(self):
        self.redis = redis_manager
        self.faq_cache_prefix = "faq:"
        self.retrieval_cache_prefix = "retrieval:"
        self.session_cache_prefix = "session:"
        
        # Cache TTL settings
        self.faq_cache_ttl = 86400  # 24 hours
        self.retrieval_cache_ttl = 3600  # 1 hour
        self.session_cache_ttl = 1800  # 30 minutes
    
    async def get_faq_cache(self, query: str, enterprise_id: UUID) -> Optional[str]:
        """
        Get cached FAQ answer for a query
        
        Args:
            query: User query
            enterprise_id: Enterprise ID
        
        Returns:
            Cached answer or None
        """
        cache_key = self._build_faq_key(query, enterprise_id)
        result = await self.redis.get(cache_key)
        
        if result:
            return result.decode('utf-8')
        
        return None
    
    async def set_faq_cache(self, query: str, enterprise_id: UUID, answer: str) -> bool:
        """
        Cache an FAQ answer
        
        Args:
            query: User query
            enterprise_id: Enterprise ID
            answer: FAQ answer
        
        Returns:
            True if cached successfully
        """
        cache_key = self._build_faq_key(query, enterprise_id)
        await self.redis.set(cache_key, answer, ex=self.faq_cache_ttl)
        return True
    
    async def get_retrieval_cache(
        self,
        query: str,
        enterprise_id: UUID,
        knowledge_base_ids: List[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached retrieval results
        
        Args:
            query: User query
            enterprise_id: Enterprise ID
            knowledge_base_ids: List of knowledge base IDs
        
        Returns:
            Cached chunks or None
        """
        cache_key = self._build_retrieval_key(query, enterprise_id, knowledge_base_ids)
        result = await self.redis.get(cache_key)
        
        if result:
            import json
            return json.loads(result.decode('utf-8'))
        
        return None
    
    async def set_retrieval_cache(
        self,
        query: str,
        enterprise_id: UUID,
        chunks: List[Dict[str, Any]],
        knowledge_base_ids: List[str] = None
    ) -> bool:
        """
        Cache retrieval results
        
        Args:
            query: User query
            enterprise_id: Enterprise ID
            chunks: Retrieved chunks
            knowledge_base_ids: List of knowledge base IDs
        
        Returns:
            True if cached successfully
        """
        cache_key = self._build_retrieval_key(query, enterprise_id, knowledge_base_ids)
        import json
        await self.redis.set(cache_key, json.dumps(chunks), ex=self.retrieval_cache_ttl)
        return True
    
    async def get_session_history(self, session_id: UUID) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached session history
        
        Args:
            session_id: Session ID
        
        Returns:
            Cached messages or None
        """
        cache_key = f"{self.session_cache_prefix}{session_id}"
        result = await self.redis.get(cache_key)
        
        if result:
            import json
            return json.loads(result.decode('utf-8'))
        
        return None
    
    async def set_session_history(self, session_id: UUID, messages: List[Dict[str, Any]]) -> bool:
        """
        Cache session history
        
        Args:
            session_id: Session ID
            messages: List of messages
        
        Returns:
            True if cached successfully
        """
        cache_key = f"{self.session_cache_prefix}{session_id}"
        import json
        await self.redis.set(cache_key, json.dumps(messages), ex=self.session_cache_ttl)
        return True
    
    async def invalidate_faq_cache(self, enterprise_id: UUID = None) -> bool:
        """
        Invalidate FAQ cache for an enterprise or all
        
        Args:
            enterprise_id: Optional enterprise filter
        
        Returns:
            True if invalidation successful
        """
        pattern = f"{self.faq_cache_prefix}*" if enterprise_id is None else \
                  f"{self.faq_cache_prefix}{enterprise_id}:*"
        
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
        
        return True
    
    async def invalidate_retrieval_cache(self, enterprise_id: UUID = None) -> bool:
        """
        Invalidate retrieval cache for an enterprise or all
        
        Args:
            enterprise_id: Optional enterprise filter
        
        Returns:
            True if invalidation successful
        """
        pattern = f"{self.retrieval_cache_prefix}*" if enterprise_id is None else \
                  f"{self.retrieval_cache_prefix}{enterprise_id}:*"
        
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
        
        return True
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache hit/miss statistics
        """
        # This would integrate with Redis INFO command in production
        return {
            "faq_cache_prefix": self.faq_cache_prefix,
            "retrieval_cache_prefix": self.retrieval_cache_prefix,
            "session_cache_prefix": self.session_cache_prefix,
            "ttl_settings": {
                "faq_cache_ttl_hours": self.faq_cache_ttl // 3600,
                "retrieval_cache_ttl_hours": self.retrieval_cache_ttl // 3600,
                "session_cache_ttl_minutes": self.session_cache_ttl // 60
            }
        }
    
    def _build_faq_key(self, query: str, enterprise_id: UUID) -> str:
        """Build cache key for FAQ"""
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()[:16]
        return f"{self.faq_cache_prefix}{enterprise_id}:{query_hash}"
    
    def _build_retrieval_key(
        self,
        query: str,
        enterprise_id: UUID,
        knowledge_base_ids: List[str] = None
    ) -> str:
        """Build cache key for retrieval results"""
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()[:16]
        
        # Include knowledge base IDs in key if provided
        kb_hash = ""
        if knowledge_base_ids:
            kb_str = "-".join(sorted(knowledge_base_ids))
            kb_hash = f":{hashlib.md5(kb_str.encode()).hexdigest()[:8]}"
        
        return f"{self.retrieval_cache_prefix}{enterprise_id}:{query_hash}{kb_hash}"


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get singleton instance of CacheService"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
