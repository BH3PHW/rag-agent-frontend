"""
FAQ匹配引擎
"""
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import re


class FAQMatcher:
    """
    FAQ强匹配引擎
    支持多种匹配策略：
    1. 关键词精确匹配
    2. 模糊匹配（编辑距离）
    3. 语义相似度（可选）
    """

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def match(
        self,
        query: str,
        faqs: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        匹配用户问题到FAQ
        返回最佳匹配的FAQ，未命中返回None
        """
        if not faqs:
            return None

        query_lower = query.lower().strip()
        query_normalized = self._normalize_text(query_lower)

        best_match = None
        best_score = 0.0

        for faq in faqs:
            if not faq.get("is_active", True):
                continue

            score = self._calculate_match_score(
                query_lower,
                query_normalized,
                faq
            )

            if score > best_score:
                best_score = score
                best_match = faq

        if best_score >= self.threshold:
            best_match["match_score"] = best_score
            return best_match

        return None

    def _calculate_match_score(
        self,
        query_lower: str,
        query_normalized: str,
        faq: Dict[str, Any]
    ) -> float:
        """
        计算匹配分数
        综合考虑：关键词匹配 > 模糊匹配 > 语义相似度
        """
        max_score = 0.0

        # 1. 关键词匹配（最高权重）
        keywords = faq.get("keywords", [])
        if keywords:
            keyword_score = self._keyword_match_score(query_lower, keywords)
            max_score = max(max_score, keyword_score * 1.0)  # 关键词权重1.0

        # 2. 精确包含匹配
        faq_question_lower = faq["question"].lower()
        if query_lower in faq_question_lower or faq_question_lower in query_lower:
            max_score = max(max_score, 0.95)

        # 3. 模糊匹配（编辑距离）
        similarity = SequenceMatcher(
            None,
            query_normalized,
            self._normalize_text(faq["question"])
        ).ratio()
        max_score = max(max_score, similarity * 0.8)  # 模糊匹配权重0.8

        return max_score

    def _keyword_match_score(self, query: str, keywords: List[str]) -> float:
        """计算关键词匹配分数"""
        query_words = set(query.split())
        matched = 0

        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in query:
                matched += 1
            elif any(word in query for word in keyword_lower.split()):
                matched += 0.5

        if not keywords:
            return 0.0

        return min(matched / len(keywords), 1.0)

    def _normalize_text(self, text: str) -> str:
        """文本标准化"""
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()

    def batch_match(
        self,
        query: str,
        faqs: List[Dict[str, Any]],
        top_k: int = 1
    ) -> List[Dict[str, Any]]:
        """
        批量匹配，返回top_k个最匹配的结果
        """
        query_lower = query.lower().strip()
        query_normalized = self._normalize_text(query_lower)

        results = []

        for faq in faqs:
            if not faq.get("is_active", True):
                continue

            score = self._calculate_match_score(
                query_lower,
                query_normalized,
                faq
            )

            if score >= 0.5:  # 阈值降低以返回更多候选
                results.append({
                    **faq,
                    "match_score": score
                })

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:top_k]


class CitationFormatter:
    """
    答案引用来源格式化器
    """

    @staticmethod
    def format_answer_with_citation(
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        格式化答案并添加引用标注

        返回：
        - 带引用的答案文本
        - 引用列表（去重）
        """
        if not sources:
            return answer, []

        formatted_answer = answer
        citations = []
        seen_docs = set()

        for i, source in enumerate(sources, 1):
            doc_id = source.get("document_id")
            doc_name = source.get("document_name", "未知文档")
            page = source.get("page")

            if doc_id and doc_id in seen_docs:
                continue

            seen_docs.add(doc_id)
            citation_text = f"[来源{i}]"

            if page:
                citation_text += f"《{doc_name}》P.{page}"
            else:
                citation_text += f"《{doc_name}》"

            if source.get("chunk_id"):
                citation_text += f" (片段{source['chunk_id'][:8]})"

            citations.append({
                "index": i,
                "document_id": doc_id,
                "document_name": doc_name,
                "page": page,
                "chunk_id": source.get("chunk_id"),
                "excerpt": source.get("content", "")[:200],
                "score": source.get("score", 0)
            })

        if citations:
            citation_line = "\n\n" + " | ".join([
                f"[{c['index']}]《{c['document_name']}》" +
                (f"P.{c['page']}" if c['page'] else "")
                for c in citations
            ])
            formatted_answer += citation_line

        return formatted_answer, citations

    @staticmethod
    def format_citation_markdown(
        sources: List[Dict[str, Any]]
    ) -> str:
        """
        生成Markdown格式的引用列表
        """
        if not sources:
            return ""

        md = "\n\n---\n**参考来源：**\n\n"

        for i, source in enumerate(sources, 1):
            doc_name = source.get("document_name", "未知文档")
            page = source.get("page")
            excerpt = source.get("content", "")

            md += f"{i}. **{doc_name}**"
            if page:
                md += f" (第{page}页)"
            md += f"\n   > {excerpt[:150]}...\n\n"

        return md


_faq_matcher = None


def get_faq_matcher() -> FAQMatcher:
    """获取FAQ匹配器单例"""
    global _faq_matcher
    if _faq_matcher is None:
        _faq_matcher = FAQMatcher()
    return _faq_matcher
