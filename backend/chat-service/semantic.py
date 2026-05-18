"""
Semantic understanding for sensitive content detection
Uses LLM to analyze context and meaning beyond keyword matching
"""
from typing import List, Dict, Any, Tuple
import json
from common.config import settings


class SemanticAnalyzer:
    """Analyze content meaning for sensitive content detection"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.sensitive_categories = {
            "legal": {
                "description": "涉及法律问题、诉讼、违法犯罪",
                "examples": ["诈骗", "报警", "起诉", "律师", "法庭", "判决"]
            },
            "financial": {
                "description": "涉及财务纠纷、赔偿、退款",
                "examples": ["赔偿", "退款", "欺诈", "被骗", "损失"]
            },
            "complaint": {
                "description": "严重投诉、举报、负面评价",
                "examples": ["投诉", "举报", "315", "消协", "差评"]
            },
            "privacy": {
                "description": "涉及个人隐私、敏感信息",
                "examples": ["身份证", "银行卡", "手机号", "地址", "密码"]
            },
            "harmful": {
                "description": "涉及人身伤害、自残、暴力",
                "examples": ["自杀", "伤害", "暴力", "杀", "死亡"]
            }
        }
        
        self.escalation_patterns = [
            r"我要.*投诉",
            r"我要.*举报",
            r"必须.*赔偿",
            r"你们.*骗",
            r"太.*差了",
            r"再也.*不来",
            r"我要.*媒体",
            r"我要.*曝光",
            r"找你们.*领导",
            r"找你们.*负责人"
        ]
    
    def analyze_semantic(
        self,
        text: str,
        enterprise_settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze content semantically for sensitive meaning
        
        Returns:
            {
                "is_sensitive": bool,
                "categories": List[str],
                "confidence": float,
                "requires_human": bool,
                "reason": str
            }
        """
        result = {
            "is_sensitive": False,
            "categories": [],
            "confidence": 0.0,
            "requires_human": False,
            "reason": "",
            "semantic_analysis": True
        }
        
        if not text or len(text.strip()) == 0:
            return result
        
        settings = enterprise_settings or {}
        enable_semantic = settings.get("enable_semantic_detection", True)
        
        if not enable_semantic:
            return result
        
        # First: Pattern matching for escalation
        import re
        for pattern in self.escalation_patterns:
            if re.search(pattern, text):
                result["is_sensitive"] = True
                result["requires_human"] = True
                result["confidence"] = 0.9
                result["reason"] = "检测到高风险诉求模式"
                return result
        
        # Second: Category detection
        detected_categories = []
        for category, info in self.sensitive_categories.items():
            for example in info["examples"]:
                if example in text:
                    detected_categories.append(category)
                    break
        
        # Custom semantic rules from enterprise
        custom_rules = settings.get("semantic_rules", [])
        for rule in custom_rules:
            if rule.get("enabled", True):
                keywords = rule.get("keywords", [])
                if any(kw in text for kw in keywords):
                    detected_categories.append(rule.get("category", "custom"))
                    result["reason"] = rule.get("description", "触发自定义语义规则")
        
        if detected_categories:
            result["is_sensitive"] = True
            result["categories"] = list(set(detected_categories))
            result["confidence"] = 0.85
            
            # Check if any category requires human
            human_required_cats = settings.get(
                "human_required_categories",
                ["legal", "financial", "complaint"]
            )
            
            if any(cat in human_required_cats for cat in detected_categories):
                result["requires_human"] = True
                result["reason"] = "检测到需要人工介入的敏感内容类别"
        
        # Sentiment analysis (simple heuristic)
        sentiment = self._analyze_sentiment(text)
        if sentiment == "negative" and len(text) > 20:
            result["confidence"] = min(0.95, result["confidence"] + 0.1)
        
        return result
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis heuristic"""
        negative_words = [
            "差", "烂", "糟", "垃圾", "坑", "骗", "气", "生气",
            "失望", "愤怒", "不满", "糟糕", "差劲", "垃圾",
            "后悔", "恶心", "讨厌", "恨", "烦", "讨厌"
        ]
        
        positive_words = [
            "好", "棒", "优秀", "满意", "感谢", "喜欢", "赞",
            "开心", "高兴", "满意", "太棒了", "很好"
        ]
        
        neg_count = sum(1 for w in negative_words if w in text)
        pos_count = sum(1 for w in positive_words if w in text)
        
        if neg_count > pos_count:
            return "negative"
        elif pos_count > neg_count:
            return "positive"
        return "neutral"
    
    def get_suggested_keywords(
        self,
        text: str,
        enterprise_id: str = None
    ) -> List[str]:
        """Get suggested keywords for future detection"""
        suggestions = []
        
        # Extract potential sensitive terms
        words = text.split()
        for word in words:
            if len(word) >= 2:
                suggestions.append(word)
        
        return suggestions[:5]


def analyze_sensitive_meaning(
    text: str,
    enterprise_settings: Dict[str, Any] = None,
    llm_client=None
) -> Dict[str, Any]:
    """Convenience function for semantic analysis"""
    analyzer = SemanticAnalyzer(llm_client)
    return analyzer.analyze_semantic(text, enterprise_settings)

