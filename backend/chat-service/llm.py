"""
LLM integration with Qwen (阿里云千问) - 流式输出版本
支持同步返回和流式输出两种模式
"""
import httpx
import json
from typing import Dict, Any, Optional, AsyncGenerator
from common.config import settings


class QwenClient:
    """Client for Alibaba Cloud Qwen API"""
    
    def __init__(
        self,
        api_key: str = None,
        endpoint: str = None,
        model: str = None
    ):
        self.api_key = api_key or settings.QWEN_API_KEY
        self.endpoint = endpoint or settings.QWEN_API_ENDPOINT
        self.model = model or settings.QWEN_MODEL
        self.temperature = settings.QWEN_TEMPERATURE
        self.max_tokens = settings.QWEN_MAX_TOKENS
    
    async def generate(
        self,
        prompt: str,
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """Generate text using Qwen API (non-streaming)"""
        if not self.api_key:
            return {
                "success": False,
                "error": "API key not configured",
                "content": "抱歉，AI服务暂时不可用。请稍后再试。"
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "success": True,
                    "content": result.get("output", {}).get("text", ""),
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "content": "抱歉，AI服务暂时不可用。"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "抱歉，服务暂时不可用。请稍后再试。"
            }
    
    async def generate_stream(
        self,
        prompt: str,
        temperature: float = None,
        max_tokens: int = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate text using Qwen API with streaming (SSE format)
        
        Yields:
            - { "content": "text chunk", "finish_reason": null, "usage": null }
            - ... more chunks ...
            - { "content": "", "finish_reason": "stop", "usage": { "total_tokens": 100 } }
        """
        if not self.api_key:
            yield {
                "content": "抱歉，AI服务暂时不可用。",
                "finish_reason": "stop",
                "usage": None
            }
            return
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
        
        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "incremental_output": True  # 启用增量输出
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    self.endpoint,
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                
                                # 处理阿里云百炼 API 的流式响应格式
                                output = data.get("output", {})
                                finish_reason = output.get("finish_reason")
                                
                                if output.get("text"):
                                    content = output.get("text", "")
                                    
                                    # 获取 token 使用统计（通常在最后一个响应中）
                                    usage = data.get("usage")
                                    
                                    yield {
                                        "content": content,
                                        "finish_reason": finish_reason,
                                        "usage": usage
                                    }
                            except json.JSONDecodeError:
                                continue
            
        except httpx.HTTPStatusError as e:
            yield {
                "content": f"服务错误：{e.response.status_code}",
                "finish_reason": "error",
                "usage": None
            }
        except httpx.ReadTimeout:
            yield {
                "content": "抱歉，响应超时了。请稍后再试。",
                "finish_reason": "timeout",
                "usage": None
            }
        except Exception as e:
            yield {
                "content": f"抱歉，出现了一个问题：{str(e)}",
                "finish_reason": "error",
                "usage": None
            }


def get_qwen_client(
    api_key: str = None,
    model: str = None
) -> QwenClient:
    """Get Qwen client with optional custom config"""
    return QwenClient(api_key=api_key, model=model)
