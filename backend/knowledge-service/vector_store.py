"""
ChromaDB vector store operations
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from common.config import settings
from knowledge_service.embeddings import generate_embeddings


class VectorStore:
    """ChromaDB vector store manager"""
    
    def __init__(self):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=".chroma_db"
        ))
    
    def get_collection(self, enterprise_id: str):
        """Get or create collection for enterprise"""
        collection_name = f"enterprise_{enterprise_id}"
        
        try:
            return self.client.get_collection(name=collection_name)
        except:
            return self.client.create_collection(
                name=collection_name,
                metadata={"enterprise_id": enterprise_id}
            )
    
    def add_chunks(
        self,
        enterprise_id: str,
        knowledge_base_id: str,
        chunks: List[Dict[str, Any]]
    ) -> bool:
        """Add chunks to vector store"""
        if not chunks:
            return True
        
        collection = self.get_collection(enterprise_id)
        
        ids = [f"{knowledge_base_id}_{c['chunk_id']}" for c in chunks]
        documents = [c["content"] for c in chunks]
        embeddings = generate_embeddings(documents)
        metadatas = [
            {
                "knowledge_base_id": knowledge_base_id,
                **c.get("metadata", {})
            }
            for c in chunks
        ]
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return True
    
    def similarity_search(
        self,
        enterprise_id: str,
        query: str,
        knowledge_base_id: Optional[str] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Search similar chunks"""
        collection = self.get_collection(enterprise_id)
        
        try:
            where_filter = {"knowledge_base_id": knowledge_base_id} if knowledge_base_id else None
            
            results = collection.query(
                query_embeddings=generate_embeddings([query]),
                n_results=top_k or settings.TOP_K,
                where=where_filter
            )
            
            chunks = []
            if results and "documents" in results and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    chunk = {
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if "metadatas" in results and i < len(results["metadatas"][0]) else {},
                        "distance": results["distances"][0][i] if "distances" in results and i < len(results["distances"][0]) else None
                    }
                    chunks.append(chunk)
            
            return chunks
        except Exception as e:
            print(f"Vector search error: {e}")
            return []
    
    def delete_chunks(self, enterprise_id: str, knowledge_base_id: str) -> bool:
        """Delete all chunks for a knowledge base"""
        collection = self.get_collection(enterprise_id)
        
        try:
            collection.delete(where={"knowledge_base_id": knowledge_base_id})
            return True
        except Exception as e:
            print(f"Delete chunks error: {e}")
            return False
    
    def delete_document(self, enterprise_id: str, document_id: str) -> bool:
        """Delete chunks for a specific document"""
        collection = self.get_collection(enterprise_id)
        
        try:
            collection.delete(where={"document_id": document_id})
            return True
        except Exception as e:
            print(f"Delete document error: {e}")
            return False


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create vector store singleton"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
