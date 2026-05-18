"""
后端测试模块
============

包含所有后端微服务的测试用例

使用方法：
    cd backend/tests
    python3 debug_services.py all        # 测试所有服务
    python3 test_api_gateway.py          # 测试API Gateway
    python3 test_user_service.py         # 测试用户服务
    python3 test_chat_service.py         # 测试聊天服务
    python3 test_knowledge_service.py    # 测试知识库服务

作者：RAG客服系统开发团队
版本：1.0.0
"""

# 版本信息
__version__ = "1.0.0"

# 导出的测试模块
__all__ = [
    'debug_services',
    'test_api_gateway',
    'test_user_service',
    'test_chat_service',
    'test_knowledge_service',
]
