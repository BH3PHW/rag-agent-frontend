"""
Rerank module for improving RAG retrieval quality
Uses cross-encoder model to re-rank retrieved chunks
"""
from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder
import numpy as np


class Reranker:
    """Rerank retrieved chunks using cross-encoder model"""

    def __init__(
        self,
        model_name: str = "shibing624/text2vec-base-chinese",
        use_pretrained: bool = True
    ):
        self.model_name = model_name
        self.use_pretrained = use_pretrained
        self._model = None

    @property
    def model(self):
        """Lazy load cross-encoder model"""
        if self._model is None:
            try:
                self._model = CrossEncoder(
                    self.model_name,
                    max_length=512
                )
            except Exception as e:
                print(f"Warning: Failed to load cross-encoder model: {e}")
                self._model = None
        return self._model

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5,
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks using cross-encoder model.

        Args:
            query: The user query
            chunks: List of retrieved chunks with 'content' field
            top_k: Number of top results to return
            batch_size: Batch size for inference

        Returns:
            Reranked list of chunks with relevance scores
        """
        if not chunks or not self.model:
            return chunks[:top_k]

        try:
            chunk_texts = [chunk.get("content", "") for chunk in chunks]

            query_chunk_pairs = [[query, text] for text in chunk_texts]

            scores = self.model.predict(
                query_chunk_pairs,
                batch_size=batch_size,
                show_progress_bar=False
            )

            if isinstance(scores, np.ndarray):
                scores = scores.tolist()

            for i, chunk in enumerate(chunks):
                chunk["rerank_score"] = float(scores[i])
                chunk["original_score"] = chunk.get("distance", 0.0)
                chunk["combined_score"] = (
                    0.4 * (1 - chunk.get("distance", 0)) +
                    0.6 * float(scores[i])
                )

            reranked = sorted(
                chunks,
                key=lambda x: x.get("combined_score", 0),
                reverse=True
            )

            for i, chunk in enumerate(reranked):
                chunk["rerank_rank"] = i + 1

            return reranked[:top_k]

        except Exception as e:
            print(f"Reranking failed: {e}, returning original order")
            return chunks[:top_k]

    def get_relevance_scores(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        """
        Get relevance scores for query-text pairs.

        Args:
            query: The query string
            texts: List of text strings

        Returns:
            List of relevance scores
        """
        if not self.model:
            return [0.0] * len(texts)

        try:
            pairs = [[query, text] for text in texts]
            scores = self.model.predict(pairs, show_progress_bar=False)

            if isinstance(scores, np.ndarray):
                return scores.tolist()
            return list(scores)

        except Exception as e:
            print(f"Scoring failed: {e}")
            return [0.0] * len(texts)


class SimpleReranker:
    """Simple rule-based reranker (fallback when cross-encoder unavailable)"""

    def __init__(self):
        self.exact_match_weight = 2.0
        self.keyword_weights = {
            "how": 1.5,
            "what": 1.5,
            "why": 1.5,
            "when": 1.5,
            "where": 1.5,
            "who": 1.5,
            "多少": 1.3,
            "怎么": 1.3,
            "什么": 1.3,
            "为什么": 1.3,
            "如何": 1.3,
        }

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Simple rule-based reranking.

        Args:
            query: The user query
            chunks: List of retrieved chunks
            top_k: Number of top results to return

        Returns:
            Reranked list of chunks
        """
        if not chunks:
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())

        for chunk in chunks:
            content_lower = chunk.get("content", "").lower()

            exact_matches = sum(
                1 for word in query_words
                if word in content_lower
            )

            keyword_bonus = 0.0
            for keyword, weight in self.keyword_weights.items():
                if keyword in query_lower and keyword in content_lower:
                    keyword_bonus += weight

            base_score = 1 - chunk.get("distance", 0)

            rerank_score = (
                base_score +
                (exact_matches * self.exact_match_weight) +
                keyword_bonus
            )

            chunk["rerank_score"] = rerank_score
            chunk["combined_score"] = rerank_score

        reranked = sorted(
            chunks,
            key=lambda x: x.get("combined_score", 0),
            reverse=True
        )

        for i, chunk in enumerate(reranked):
            chunk["rerank_rank"] = i + 1

        return reranked[:top_k]


_reranker: Optional[Reranker] = None
_simple_reranker: Optional[SimpleReranker] = None


def get_reranker(use_cross_encoder: bool = True) -> Any:
    """
    Get reranker instance.

    Args:
        use_cross_encoder: Whether to use cross-encoder (True) or simple reranker (False)

    Returns:
        Reranker or SimpleReranker instance
    """
    global _reranker, _simple_reranker

    if use_cross_encoder:
        if _reranker is None:
            _reranker = Reranker()
        return _reranker
    else:
        if _simple_reranker is None:
            _simple_reranker = SimpleReranker()
        return _simple_reranker


def rerank_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 5,
    use_cross_encoder: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function for reranking chunks.

    Args:
        query: User query
        chunks: Retrieved chunks
        top_k: Number of results to return
        use_cross_encoder: Use cross-encoder or simple reranker

    Returns:
        Reranked chunks
    """
    reranker = get_reranker(use_cross_encoder)
    return reranker.rerank(query, chunks, top_k)
