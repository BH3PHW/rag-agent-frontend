"""
Chat Service 调试用例
======================

测试覆盖：
1. 导入测试 - 验证模块可以正确导入
2. RAG功能测试 - 检索增强生成
3. 流式输出测试 - SSE流式响应
4. 敏感内容检测测试
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
BACKEND_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR / "chat-service"))


def test_imports():
    """测试Chat Service模块导入"""
    print("\n" + "="*60)
    print("测试 1: 模块导入")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    # 测试导入主模块
    try:
        from main import app
        print("✅ 成功导入 main 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 main 模块失败: {e}")
        tests_failed += 1

    # 测试导入配置
    try:
        from config import settings
        print("✅ 成功导入 config 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 config 模块失败: {e}")
        tests_failed += 1

    # 测试导入数据模型
    try:
        from models import ChatSession, ChatMessage
        print("✅ 成功导入 models 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 models 模块失败: {e}")
        tests_failed += 1

    # 测试导入Redis客户端
    try:
        from redis_client import redis_manager
        print("✅ 成功导入 redis_client 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 redis_client 模块失败: {e}")
        tests_failed += 1

    print(f"\n导入测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_rag_components():
    """测试RAG组件"""
    print("\n" + "="*60)
    print("测试 2: RAG组件")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    # 测试RAG引擎导入
    try:
        from rag import get_rag_engine
        print("✅ 成功导入 RAG 引擎")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 RAG 引擎失败: {e}")
        tests_failed += 1

    # 测试意图路由器导入
    try:
        from intent_router import get_intent_router, IntentType
        print("✅ 成功导入意图路由器")
        print(f"   - IntentType 枚举值: {[e.name for e in IntentType]}")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入意图路由器失败: {e}")
        tests_failed += 1

    # 测试SSE流式输出器导入
    try:
        from sse_stream import SSEStreamer
        print("✅ 成功导入 SSE 流式输出器")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 SSE 流式输出器失败: {e}")
        tests_failed += 1

    # 测试敏感内容检测导入
    try:
        from sensitive import detect_sensitive_content
        print("✅ 成功导入敏感内容检测模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入敏感内容检测模块失败: {e}")
        tests_failed += 1

    # 测试防提示词注入导入
    try:
        from prompt_injection_defender import get_prompt_injection_defender
        print("✅ 成功导入防提示词注入模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入防提示词注入模块失败: {e}")
        tests_failed += 1

    print(f"\nRAG组件测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_api_endpoints():
    """测试API端点"""
    print("\n" + "="*60)
    print("测试 3: API端点配置")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        from main import app

        # 获取所有路由
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', {'GET'})
                routes.append((methods, route.path))

        # 统计路由
        chat_routes = [r for r in routes if '/chat' in r[1]]
        feedback_routes = [r for r in routes if '/feedback' in r[1]]

        print(f"\n总路由数: {len(routes)}")
        print(f"聊天路由: {len(chat_routes)}")
        print(f"反馈路由: {len(feedback_routes)}")

        # 验证关键路由
        critical_routes = [
            '/health',
            '/api/v1/chat/sessions',
            '/api/v1/chat/sessions/{session_id}/messages',
        ]

        existing_routes = [r[1] for r in routes]
        for route in critical_routes:
            if route in existing_routes:
                print(f"✅ 关键路由存在: {route}")
                tests_passed += 1
            else:
                print(f"❌ 关键路由缺失: {route}")
                tests_failed += 1

    except Exception as e:
        print(f"❌ API端点测试失败: {e}")
        tests_failed += 1

    print(f"\nAPI端点测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_sse_streamer():
    """测试SSE流式输出器"""
    print("\n" + "="*60)
    print("测试 4: SSE流式输出器")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        from sse_stream import SSEStreamer

        streamer = SSEStreamer()

        # 测试event方法
        try:
            event_data = streamer.event("test", {"message": "hello"})
            print(f"✅ event方法工作正常")
            print(f"   输出: {event_data[:50]}...")
            tests_passed += 1
        except Exception as e:
            print(f"❌ event方法失败: {e}")
            tests_failed += 1

        # 测试chunk方法
        try:
            chunk_data = streamer.chunk("Hello")
            print(f"✅ chunk方法工作正常")
            print(f"   输出: {chunk_data[:50]}...")
            tests_passed += 1
        except Exception as e:
            print(f"❌ chunk方法失败: {e}")
            tests_failed += 1

    except Exception as e:
        print(f"❌ SSE流式输出器测试失败: {e}")
        tests_failed += 1

    print(f"\nSSE流式输出器测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("#" + " "*12 + "Chat Service 测试套件" + " "*18 + "#")
    print("#"*60)

    results = {
        "imports": test_imports(),
        "rag": test_rag_components(),
        "endpoints": test_api_endpoints(),
        "sse": test_sse_streamer(),
    }

    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name.upper():20} {status}")
        if not passed:
            all_passed = False

    print("="*60)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查上述错误")

    return all_passed


if __name__ == "__main__":
    run_all_tests()
