# 练习06: 简单聊天API
# 运行: python practice_06_simple_chat_api.py
# 访问: http://localhost:8080/docs

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="练习06 - 简单聊天API")

# 数据模型
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    message: str

# 存储会话
chat_sessions = {}

def get_bot_response(message: str) -> str:
    """获取机器人回复"""
    responses = {
        "你好": "你好！我是智能客服，有什么可以帮你的？",
        "帮助": "我可以帮你回答常见问题！",
        "再见": "再见，有问题随时回来！",
        "退货": "请在订单页面申请退货",
        "配送": "通常24小时内发货，3-5天送达"
    }
    return responses.get(message, "抱歉，我不太明白你说的，能换一种说法吗？")

# 创建会话
@app.post("/api/sessions/{user_id}")
async def create_session(user_id: str):
    """创建新的聊天会话"""
    session_id = f"session_{user_id}"
    chat_sessions[session_id] = []
    return {
        "success": True,
        "session_id": session_id,
        "message": "会话创建成功"
    }

# 发送消息
@app.post("/api/sessions/{session_id}/chat")
async def send_chat_message(session_id: str, request: ChatRequest):
    """发送聊天消息并获取回复"""
    if session_id not in chat_sessions:
        return {
            "success": False,
            "error": "会话不存在"
        }
    
    # 保存用户消息
    user_msg = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    chat_sessions[session_id].append(user_msg)
    
    # 获取机器人回复
    bot_response = get_bot_response(request.message)
    
    # 保存机器人回复
    bot_msg = ChatMessage(
        role="assistant",
        content=bot_response,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    chat_sessions[session_id].append(bot_msg)
    
    return {
        "success": True,
        "response": bot_response,
        "message": bot_msg
    }

# 获取聊天历史
@app.get("/api/sessions/{session_id}/history", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    """获取聊天历史"""
    if session_id not in chat_sessions:
        return []
    return chat_sessions[session_id]

# 根路径
@app.get("/")
async def root():
    return {
        "message": "欢迎来到练习06 - 简单聊天API",
        "docs": "/docs",
        "usage": "先创建会话，然后发送消息！"
    }

# 运行服务器
if __name__ == "__main__":
    import uvicorn
    print("=" * 40)
    print("🤖 聊天API服务器启动在 http://localhost:8080")
    print("📚 API文档: http://localhost:8080/docs")
    print("=" * 40)
    uvicorn.run(app, host="0.0.0.0", port=8080)
