"""
Server-Sent Events (SSE) Streaming Module
流式输出核心模块
"""
import json
from typing import Dict, Any, AsyncGenerator, Optional
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session


class SSEStreamer:
    """SSE 流式输出器"""
    
    @staticmethod
    def format_event(data: Dict[str, Any], event_type: str = None) -> str:
        """
        格式化 SSE 事件
        
        Args:
            data: 事件数据
            event_type: 可选的事件类型
            
        Returns:
            SSE 格式的字符串: "data: {json}\\n\\n"
        """
        sse_parts = []
        if event_type:
            sse_parts.append(f"event: {event_type}")
        sse_parts.append(f"data: {json.dumps(data, ensure_ascii=False)}")
        return "\n".join(sse_parts) + "\n\n"
    
    @staticmethod
    async def generate_sse_stream(
        llm_generator: AsyncGenerator[Dict[str, Any], None],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        生成完整的 SSE 流
        
        Args:
            llm_generator: LLM 流式生成器
            metadata: 可选的元数据（sources等）
            
        Yields:
            SSE 格式的字符串
        """
        # 1. 发送开始事件
        start_event = {
            "type": "start",
            "timestamp": datetime.utcnow().isoformat()
        }
        if metadata:
            start_event.update(metadata)
        yield SSEStreamer.format_event(start_event)
        
        # 2. 流式发送 LLM 内容
        full_content = ""
        finish_reason = None
        usage = None
        
        try:
            async for chunk in llm_generator:
                content = chunk.get("content", "")
                finish_reason = chunk.get("finish_reason")
                usage = chunk.get("usage")
                
                if content:
                    full_content += content
                    
                    # 发送内容块
                    chunk_event = {
                        "type": "content",
                        "content": content,
                        "finish_reason": finish_reason
                    }
                    yield SSEStreamer.format_event(chunk_event)
                
                if finish_reason:
                    break
        
        except Exception as e:
            # 发送错误事件
            error_event = {
                "type": "error",
                "error": str(e),
                "code": "STREAM_ERROR"
            }
            yield SSEStreamer.format_event(error_event)
            return
        
        # 3. 发送结束事件
        end_event = {
            "type": "end",
            "finish_reason": finish_reason,
            "full_content": full_content,
            "usage": usage,
            "timestamp": datetime.utcnow().isoformat()
        }
        yield SSEStreamer.format_event(end_event)
    
    @staticmethod
    async def generate_simple_response(content: str) -> AsyncGenerator[str, None]:
        """
        生成简单的一次性响应（用于 FAQ、意图路由等不需要 LLM 的情况）
        
        Args:
            content: 完整的响应内容
            
        Yields:
            SSE 格式的字符串
        """
        # 开始事件
        yield SSEStreamer.format_event({
            "type": "start",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 内容事件
        yield SSEStreamer.format_event({
            "type": "content",
            "content": content,
            "finish_reason": None
        })
        
        # 结束事件
        yield SSEStreamer.format_event({
            "type": "end",
            "finish_reason": "none",
            "full_content": content,
            "usage": None,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def generate_error_response(error_message: str, error_code: str = "ERROR") -> AsyncGenerator[str, None]:
        """
        生成错误响应
        
        Args:
            error_message: 错误消息
            error_code: 错误码
            
        Yields:
            SSE 格式的字符串
        """
        yield SSEStreamer.format_event({
            "type": "start",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        yield SSEStreamer.format_event({
            "type": "error",
            "error": error_message,
            "code": error_code
        })
        
        yield SSEStreamer.format_event({
            "type": "end",
            "finish_reason": "error",
            "full_content": error_message,
            "usage": None,
            "timestamp": datetime.utcnow().isoformat()
        })
