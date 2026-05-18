"""
意图识别与路由引擎
用于拦截闲聊和简单指令，避免每次都调用昂贵的 Qwen 大模型

架构设计：
1. 规则匹配层：快速识别闲聊、寒暄、简单指令（零成本）
2. 实体提取层：从业务查询中提取关键实体
3. 路由决策层：根据意图决定是否调用 RAG/LLM
4. 成本统计层：记录每次请求的路由结果，计算 Token 节省
"""
from typing import Dict, Any, List, Optional, Tuple, Callable
from enum import Enum
import re
import json
import time
import random
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


class IntentType(Enum):
    """意图类型枚举"""
    GREETING = "greeting"           # 寒暄
    THANKS = "thanks"              # 感谢
    FAREWELL = "farewell"          # 告别
    ORDER_QUERY = "order_query"     # 订单查询
    PRODUCT_QUERY = "product_query" # 产品查询
    COMPLAINT = "complaint"        # 投诉
    FAQ = "faq"                    # FAQ匹配
    RAG = "rag"                    # RAG检索（复杂咨询）
    HUMAN = "human"                # 转人工
    UNKNOWN = "unknown"            # 未知/复杂问题


class CostTier(Enum):
    """成本等级"""
    FREE = 0        # 免费（规则响应）
    LOW = 1         # 低成本（简单处理）
    MEDIUM = 2      # 中等成本（部分LLM调用）
    HIGH = 3        # 高成本（完整RAG+LLM）


@dataclass
class IntentDecision:
    """意图路由决策"""
    intent: IntentType
    cost_tier: CostTier
    should_use_llm: bool
    should_use_rag: bool
    should_escalate: bool
    confidence: float
    response: Optional[str] = None
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "cost_tier": self.cost_tier.name,
            "should_use_llm": self.should_use_llm,
            "should_use_rag": self.should_use_rag,
            "should_escalate": self.should_escalate,
            "confidence": round(self.confidence, 3),
            "response": self.response,
            "extracted_entities": self.extracted_entities,
            "reasoning": self.reasoning
        }


@dataclass
class RouteLog:
    """路由日志"""
    request_id: str
    timestamp: datetime
    query: str
    intent: IntentType
    cost_tier: CostTier
    llm_called: bool
    tokens_used: int = 0
    estimated_cost_saved: float = 0.0
    response_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "query": self.query,
            "intent": self.intent.value,
            "cost_tier": self.cost_tier.name,
            "llm_called": self.llm_called,
            "tokens_used": self.tokens_used,
            "estimated_cost_saved": round(self.estimated_cost_saved, 4),
            "response_time_ms": self.response_time_ms
        }


class IntentRule:
    """
    意图路由规则定义
    使用正则表达式进行快速匹配
    """

    GREETING_PATTERNS = [
        r"^(你好|您好|hi|hello|hey|hallo|hi!|hello!)$",
        r"^(在|在吗|在吗？|在不在)$",
        r"^(早上好|下午好|晚上好|早安|晚安)$",
        r"^(嘿|哈喽|嗨|salutation)$",
    ]

    THANKS_PATTERNS = [
        r"^(谢谢|感谢|多谢|谢了|谢谢您)$",
        r"^(太感谢了|非常感谢|十分感谢|多谢了)$",
        r"^(感恩|感激不尽)$",
    ]

    FAREWELL_PATTERNS = [
        r"^(再见|拜拜|拜|下次见|回头见|走了)$",
        r"^(我先走了|先这样|就这样|先撤了)$",
        r"^(拜拜!|再见!|下次再聊)$",
    ]

    ORDER_PATTERNS = [
        r"(订单|单号|快递|发货|物流)",
        r"(什么时候到|什么时候发货|发货了吗)",
        r"(查订单|看订单|我的订单)",
    ]

    PRODUCT_PATTERNS = [
        r"(产品|型号|规格|参数)",
        r"(多少钱|价格|报价)",
        r"(有什么|哪种|哪个好)",
    ]

    HUMAN_PATTERNS = [
        r"(人工|客服|真人|转人工|我要投诉)",
        r"(经理|主管|负责人|专业人士)",
        r"(人工客服|真人服务)",
    ]

    COMPLAINT_PATTERNS = [
        r"(差|烂|垃圾|骗子|退款|退货|赔偿|坑)",
        r"(举报|投诉|曝光|报警|太差)",
        r"(不满意|不靠谱|不行|没用)",
    ]

    @classmethod
    def match(cls, text: str) -> Optional[IntentType]:
        """根据文本内容匹配意图类型"""
        text_lower = text.lower().strip()

        if cls._match_patterns(text_lower, cls.GREETING_PATTERNS):
            return IntentType.GREETING

        if cls._match_patterns(text_lower, cls.THANKS_PATTERNS):
            return IntentType.THANKS

        if cls._match_patterns(text_lower, cls.FAREWELL_PATTERNS):
            return IntentType.FAREWELL

        if cls._match_patterns(text_lower, cls.ORDER_PATTERNS):
            return IntentType.ORDER_QUERY

        if cls._match_patterns(text_lower, cls.PRODUCT_PATTERNS):
            return IntentType.PRODUCT_QUERY

        if cls._match_patterns(text_lower, cls.COMPLAINT_PATTERNS):
            return IntentType.COMPLAINT

        if cls._match_patterns(text_lower, cls.HUMAN_PATTERNS):
            return IntentType.HUMAN

        return None

    @classmethod
    def _match_patterns(cls, text: str, patterns: List[str]) -> bool:
        """检查文本是否匹配任一模式"""
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False

    @classmethod
    def extract_entities(cls, text: str, intent: IntentType) -> Dict[str, Any]:
        """根据意图类型提取关键实体"""
        entities = {}

        if intent == IntentType.ORDER_QUERY:
            order_id_match = re.search(r"([A-Z0-9]{8,})", text)
            if order_id_match:
                entities["order_id"] = order_id_match.group(1)

            phone_match = re.search(r"1[3-9]\d{9}", text)
            if phone_match:
                entities["phone"] = phone_match.group()

        elif intent == IntentType.PRODUCT_QUERY:
            product_patterns = [
                (r"(A\d+|X\d+|Pro|Max)", "model_series"),
                (r"(\d+)寸|(\d+)英寸", "size"),
                (r"(\d+)元|(\d+)块", "price_range"),
            ]
            for pattern, entity_type in product_patterns:
                match = re.search(pattern, text)
                if match:
                    entities[entity_type] = match.group()

        return entities


class IntentRouter:
    """
    意图路由器核心类

    功能：
    1. 意图识别：通过规则快速分类用户意图
    2. 路由决策：决定是否调用 LLM/RAG
    3. 成本优化：计算并记录 Token 节省
    4. 日志追踪：记录每次请求的路由结果

    使用 FastAPI 依赖注入或中间件调用
    """

    # 预设回复库
    GREETING_RESPONSES = [
        "您好！我是智能客服，很高兴为您服务。请问有什么可以帮您？",
        "您好！请问有什么问题需要咨询吗？我随时为您提供帮助。",
        "Hello！很高兴为您服务。有什么可以帮到您的吗？",
        "你好！欢迎使用智能客服系统。请问需要什么帮助？",
    ]

    THANKS_RESPONSES = [
        "不客气！很高兴能帮到您。请问还有其他问题吗？",
        "谢谢您的认可！如有任何疑问，随时联系我。",
        "您客气了！很高兴能为您服务。再见！",
    ]

    FAREWELL_RESPONSES = [
        "再见！祝您生活愉快！如有需要随时联系我。",
        "好的，再见！期待下次为您服务。",
        "拜拜！祝您一切顺利！",
        "再见，感谢您的使用！有问题随时找我。",
    ]

    ORDER_QUERY_RESPONSE = "我理解您想查询订单相关问题。请提供您的订单号或手机尾号，我将为您查询订单状态。"

    PRODUCT_QUERY_RESPONSE = "我理解您想了解产品相关信息。请告诉我想查询哪款产品的具体信息？"

    HUMAN_RESPONSE = "我理解您需要人工客服的帮助。我已通知客服人员，他们将尽快与您联系。请稍候片刻，感谢您的耐心。"

    # Token 成本估算（基于 Qwen Turbo）
    COST_PER_TOKEN = 0.002  # 每 Token 成本（元）
    AVG_QUERY_TOKENS = 500   # 平均查询 Token 数
    AVG_RESPONSE_TOKENS = 300  # 平均响应 Token 数

    def __init__(self):
        self.rule = IntentRule()
        self.route_logs: List[RouteLog] = []

    def classify(self, query: str) -> IntentDecision:
        """
        意图分类主方法

        参数：
            query: 用户查询文本

        返回：
            IntentDecision: 包含路由决策的意图决策对象
        """
        start_time = time.time()
        intent = self.rule.match(query) or IntentType.UNKNOWN
        entities = self.rule.extract_entities(query, intent)

        decision = self._make_decision(query, intent, entities)
        decision.reasoning = f"识别耗时: {round((time.time() - start_time) * 1000)}ms"

        return decision

    def _make_decision(
        self,
        query: str,
        intent: IntentType,
        entities: Dict[str, Any]
    ) -> IntentDecision:
        """根据意图类型生成路由决策"""

        if intent == IntentType.GREETING:
            return IntentDecision(
                intent=intent,
                cost_tier=CostTier.FREE,
                should_use_llm=False,
                should_use_rag=False,
                should_escalate=False,
                confidence=0.95,
                response=random.choice(self.GREETING_RESPONSES),
                extracted_entities=entities,
                reasoning="闲聊寒暄，使用预设回复"
            )

        elif intent == IntentType.THANKS:
            return IntentDecision(
                intent=intent,
                cost_tier=CostTier.FREE,
                should_use_llm=False,
                should_use_rag=False,
                should_escalate=False,
                confidence=0.95,
                response=random.choice(self.THANKS_RESPONSES),
                extracted_entities=entities,
                reasoning="感谢回复，使用预设回复"
            )

        elif intent == IntentType.FAREWELL:
            return IntentDecision(
                intent=intent,
                cost_tier=CostTier.FREE,
                should_use_llm=False,
                should_use_rag=False,
                should_escalate=False,
                confidence=0.95,
                response=random.choice(self.FAREWELL_RESPONSES),
                extracted_entities=entities,
                reasoning="告别语，使用预设回复"
            )

        elif intent == IntentType.ORDER_QUERY:
            return IntentDecision(
                intent=intent,
                cost_tier=CostTier.LOW,
                should_use_llm=False,
                should_use_rag=False,
                should_escalate=False,
                confidence=0.9,
                response=self.ORDER_QUERY_RESPONSE,
                extracted_entities=entities,
                reasoning="订单查询，提取实体后调用业务接口"
            )

        elif intent == IntentType.PRODUCT_QUERY:
            return IntentDecision(
                intent=intent,
                cost_tier=CostTier.LOW,
                should_use_llm=False,
                should_use_rag=True,
                should_escalate=False,
                confidence=0.85,
                response=self.PRODUCT_QUERY_RESPONSE,
                extracted_entities=entities,
                reasoning="产品查询，使用 RAG 检索产品知识库"
            )

        elif intent == IntentType.COMPLAINT:
            return IntentDecision(
                intent=intent,
                cost_tier=CostTier.MEDIUM,
                should_use_llm=True,
                should_use_rag=True,
                should_escalate=True,
                confidence=0.85,
                response=None,
                extracted_entities=entities,
                reasoning="投诉内容，需要 RAG 检索 + LLM 生成 + 标记告警"
            )

        elif intent == IntentType.HUMAN:
            return IntentDecision(
                intent=intent,
                cost_tier=CostTier.LOW,
                should_use_llm=False,
                should_use_rag=False,
                should_escalate=True,
                confidence=0.9,
                response=self.HUMAN_RESPONSE,
                extracted_entities=entities,
                reasoning="转人工请求，直接转接人工客服"
            )

        else:
            return IntentDecision(
                intent=IntentType.RAG,
                cost_tier=CostTier.HIGH,
                should_use_llm=True,
                should_use_rag=True,
                should_escalate=False,
                confidence=0.7,
                response=None,
                extracted_entities={},
                reasoning="复杂咨询/知识库问答，启用完整 RAG + LLM 流程"
            )

    def calculate_cost_saved(self, decision: IntentDecision) -> float:
        """
        计算成本节省

        如果不经过意图路由直接调用 LLM 的成本
        减去当前决策的实际成本
        """
        full_llm_cost = (self.AVG_QUERY_TOKENS + self.AVG_RESPONSE_TOKENS) * self.COST_PER_TOKEN

        if decision.cost_tier == CostTier.FREE:
            return full_llm_cost
        elif decision.cost_tier == CostTier.LOW:
            return full_llm_cost * 0.3
        elif decision.cost_tier == CostTier.MEDIUM:
            return full_llm_cost * 0.5
        else:
            return 0.0

    def log_route(self, log: RouteLog):
        """记录路由日志"""
        self.route_logs.append(log)
        if len(self.route_logs) > 10000:
            self.route_logs = self.route_logs[-5000:]

    def get_cost_stats(self) -> Dict[str, Any]:
        """获取成本统计"""
        if not self.route_logs:
            return {
                "total_requests": 0,
                "total_tokens_saved": 0,
                "total_cost_saved": 0,
                "llm_call_rate": 0
            }

        total = len(self.route_logs)
        llm_calls = sum(1 for log in self.route_logs if log.llm_called)
        total_saved = sum(log.estimated_cost_saved for log in self.route_logs)

        return {
            "total_requests": total,
            "total_tokens_saved": int(total_saved / self.COST_PER_TOKEN),
            "total_cost_saved": round(total_saved, 4),
            "llm_call_rate": round(llm_calls / total * 100, 2) if total > 0 else 0,
            "intent_distribution": self._get_intent_distribution()
        }

    def _get_intent_distribution(self) -> Dict[str, int]:
        """获取意图分布"""
        dist = {}
        for log in self.route_logs:
            intent_name = log.intent.value
            dist[intent_name] = dist.get(intent_name, 0) + 1
        return dist


_intent_router: Optional[IntentRouter] = None


def get_intent_router() -> IntentRouter:
    """获取意图路由器单例"""
    global _intent_router
    if _intent_router is None:
        _intent_router = IntentRouter()
    return _intent_router
