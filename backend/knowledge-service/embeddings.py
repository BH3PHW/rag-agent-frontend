"""
Embedding utilities using HuggingFace
"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from common.config import settings


class EmbeddingModel:
    """Embedding model wrapper"""
    
    def __init__(self, model_name: str = "shibing624/text2vec-base-chinese"):
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """Lazy load model"""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model
    
    def encode(self, texts: List[str], normalize: bool = True) -> List[List[float]]:
        """Generate embeddings for texts"""
        embeddings = self.model.encode(texts, normalize_embeddings=normalize)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()


_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create embedding model singleton"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts"""
    model = get_embedding_model()
    return model.encode(texts)
