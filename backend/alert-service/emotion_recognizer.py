"""
Emotion Recognition Service
"""
from typing import Dict, Any, Tuple
import re

class EmotionRecognizer:
    """Recognize user emotions from text"""
    
    def __init__(self):
        # 情绪关键词字典
        self.emotion_keywords = {
            'angry': [
                '生气', '愤怒', '火大', '气死', '操', '靠', 'Fuck',
                '投诉', '差评', '垃圾', '没用', '骗人', '滚',
                '什么鬼', '搞什么', '太过分', '无法接受', '强烈不满',
                '严重问题', '太差了', '太烂了', '坑人', '欺骗'
            ],
            'frustrated': [
                '烦', '郁闷', '无语', '心累', '麻烦', '复杂',
                '难用', '卡顿', '加载慢', '无法登录', '一直报错',
                '搞不懂', '不会用', '太复杂', '绕来绕去', '折腾'
            ],
            'sad': [
                '难过', '伤心', '失望', '遗憾', '可惜', '损失',
                '钱没了', '白费', '浪费时间', '耽误事', '错过了'
            ],
            'urgent': [
                '紧急', '立刻', '马上', '尽快', '赶紧', '必须',
                '现在', '立刻处理', '马上解决', '十万火急', '越快越好'
            ],
            'confused': [
                '不懂', '不清楚', '不明白', '不知道', '疑惑', '困惑',
                '怎么回事', '什么意思', '这是什么', '为什么', '怎么办'
            ],
            'happy': [
                '开心', '高兴', '满意', '太好了', '谢谢', '感谢',
                '太棒了', '很有用', '解决了', '完美', '点赞'
            ]
        }
        
        # 情绪强度增强词
        self.intensifiers = [
            '非常', '特别', '十分', '极其', '真的', '实在',
            '太', '超', '巨', '好', '很', '完全', '彻底'
        ]
        
        # 情绪否定词
        self.negations = [
            '不', '没', '没有', '不是', '不要', '不用'
        ]
    
    def analyze_emotion(self, text: str) -> Dict[str, Any]:
        """
        Analyze emotion from text
        
        Args:
            text: User input text
        
        Returns:
            Dictionary with emotion analysis results
        """
        text_lower = text.lower()
        
        scores = {emotion: 0.0 for emotion in self.emotion_keywords}
        
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    base_score = 0.3
                    
                    # 检查强度增强词
                    for intensifier in self.intensifiers:
                        if intensifier in text_lower:
                            base_score *= 1.5
                    
                    # 检查否定词
                    has_negation = False
                    for negation in self.negations:
                        if negation in text_lower:
                            has_negation = True
                            break
                    
                    if has_negation:
                        base_score *= 0.3
                    
                    scores[emotion] += base_score
        
        # 归一化分数
        max_score = max(scores.values())
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}
        
        # 确定主导情绪
        dominant_emotion = max(scores, key=scores.get) if max(scores.values()) > 0.3 else 'neutral'
        overall_intensity = sum(scores.values()) / len(scores)
        
        return {
            'dominant_emotion': dominant_emotion,
            'emotion_scores': scores,
            'intensity': overall_intensity,
            'is_negative': dominant_emotion in ['angry', 'frustrated', 'sad'],
            'requires_human': dominant_emotion in ['angry', 'urgent'] and overall_intensity > 0.5
        }
    
    def detect_frustration_signals(self, conversation_history: list) -> bool:
        """
        Detect frustration signals from conversation history
        
        Args:
            conversation_history: List of message dicts with 'role' and 'content'
        
        Returns:
            True if frustration detected
        """
        if not conversation_history:
            return False
        
        # 检查连续追问次数
        user_messages = [m for m in conversation_history[-5:] if m.get('role') == 'user']
        if len(user_messages) >= 3:
            # 检查是否有重复提问或表达不满
            for msg in user_messages:
                content = msg.get('content', '')
                if any(keyword in content for keyword in ['还是', '仍然', '依然', '还是不行', '还是不懂']):
                    return True
        
        return False
