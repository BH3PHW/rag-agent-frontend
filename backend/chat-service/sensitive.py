"""
Sensitive word detection and handling
"""
from typing import List, Dict, Any, Tuple
import re
from common.config import settings


class SensitiveWordDetector:
    """Detect sensitive words and determine if human intervention is needed"""
    
    def __init__(self, custom_words: List[str] = None):
        self.default_keywords = set(settings.SENSITIVE_KEYWORDS)
        self.custom_keywords = set(custom_words or [])
        self.all_keywords = self.default_keywords | self.custom_keywords
        
        # Build regex pattern
        self.pattern = re.compile(
            "|".join([re.escape(word) for word in self.all_keywords])
        )
    
    def detect(self, text: str) -> Tuple[bool, List[str]]:
        """Detect if text contains sensitive words"""
        if not text:
            return False, []
        
        matches = self.pattern.findall(text.lower())
        unique_matches = list(set(matches))
        
        return len(unique_matches) > 0, unique_matches
    
    def analyze_context(self, text: str, trigger_words: List[str]) -> Dict[str, Any]:
        """Analyze the context of detected sensitive words"""
        analysis = {
            "severity": "low",
            "requires_human": False,
            "reasons": []
        }
        
        # Determine severity
        urgent_words = ["诈骗", "违法", "犯罪", "报警", "起诉", "律师"]
        high_priority_words = ["投诉", "举报", "赔偿", "欺诈"]
        
        if any(word in trigger_words for word in urgent_words):
            analysis["severity"] = "urgent"
            analysis["requires_human"] = True
            analysis["reasons"].append("涉及法律问题，需要人工介入")
        elif any(word in trigger_words for word in high_priority_words):
            analysis["severity"] = "high"
            analysis["requires_human"] = True
            analysis["reasons"].append("高优先级投诉，建议人工介入")
        elif len(trigger_words) >= 3:
            analysis["severity"] = "medium"
            analysis["reasons"].append("多个敏感词触发")
        
        # Check for explicit human request
        human_keywords = ["人工", "客服", "人工客服", "转人工", "真人"]
        if any(keyword in text for keyword in human_keywords):
            analysis["requires_human"] = True
            analysis["reasons"].append("用户明确要求人工服务")
        
        return analysis
    
    def should_escalate(
        self,
        consecutive_failures: int,
        user_sentiment: str = "neutral"
    ) -> bool:
        """Determine if conversation should be escalated to human"""
        if consecutive_failures >= settings.HUMAN_THRESHOLD:
            return True
        
        if user_sentiment in ["angry", "frustrated"]:
            return True
        
        return False


def detect_sensitive_content(
    text: str,
    custom_words: List[str] = None
) -> Dict[str, Any]:
    """Convenience function to detect sensitive content"""
    detector = SensitiveWordDetector(custom_words)
    is_sensitive, trigger_words = detector.detect(text)
    
    if is_sensitive:
        analysis = detector.analyze_context(text, trigger_words)
        return {
            "is_sensitive": True,
            "trigger_words": trigger_words,
            **analysis
        }
    
    return {
        "is_sensitive": False,
        "trigger_words": [],
        "severity": "none",
        "requires_human": False,
        "reasons": []
    }
