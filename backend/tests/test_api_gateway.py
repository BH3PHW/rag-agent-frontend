"""
API Gateway 调试用例
=====================

测试覆盖：
1. 导入测试 - 验证模块可以正确导入
2. 路由测试 - 验证API路由配置
3. 中间件测试 - 验证中间件配置
4. 配置测试 - 验证服务配置
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
BACKEND_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR / "api-gateway"))


def test_imports():
    """测试API Gateway模块导入"""
    print("\n" + "="*60)
    print("测试 1: 模块导入")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    # 测试导入主模块
    try:
        from main import app, proxy_request, validate_enterprise_request
        print("✅ 成功导入 main 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 main 模块失败: {e}")
        tests_failed += 1

    # 测试导入配置
    try:
        from config import settings
        print("✅ 成功导入 config 模块")
        print(f"   - CORS Origins: {settings.CORS_ORIGINS}")
        print(f"   - JWT Secret Key: {'*' * 20}")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 config 模块失败: {e}")
        tests_failed += 1

    # 测试导入安全模块
    try:
        from security import verify_token, validate_enterprise_access
        print("✅ 成功导入 security 模块")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ 导入 security 模块失败: {e}")
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


def test_routes():
    """测试API路由配置"""
    print("\n" + "="*60)
    print("测试 2: API路由配置")
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

        # 统计路由类型
        auth_routes = [r for r in routes if '/auth/' in r[1]]
        enterprise_routes = [r for r in routes if '/enterprises' in r[1]]
        knowledge_routes = [r for r in routes if '/knowledge' in r[1]]
        chat_routes = [r for r in routes if '/chat' in r[1]]
        alert_routes = [r for r in routes if '/alerts' in r[1]]
        channel_routes = [r for r in routes if '/channel' in r[1]]

        print(f"\n总路由数: {len(routes)}")
        print(f"认证路由: {len(auth_routes)}")
        print(f"企业路由: {len(enterprise_routes)}")
        print(f"知识库路由: {len(knowledge_routes)}")
        print(f"聊天路由: {len(chat_routes)}")
        print(f"告警路由: {len(alert_routes)}")
        print(f"渠道路由: {len(channel_routes)}")

        # 验证关键路由存在
        critical_routes = [
            '/',  # 根路径
            '/health',  # 健康检查
            '/api/v1/auth/login',  # 登录
            '/api/v1/auth/register',  # 注册
            '/api/v1/auth/me',  # 获取当前用户
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
        print(f"❌ 路由测试失败: {e}")
        tests_failed += 1

    print(f"\n路由测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_config():
    """测试配置"""
    print("\n" + "="*60)
    print("测试 3: 配置测试")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        from config import settings

        # 测试服务URL配置
        print("\n微服务URL配置:")
        services = {
            'USER_SERVICE_URL': settings.USER_SERVICE_URL,
            'KNOWLEDGE_SERVICE_URL': settings.KNOWLEDGE_SERVICE_URL,
            'CHAT_SERVICE_URL': settings.CHAT_SERVICE_URL,
            'ALERT_SERVICE_URL': settings.ALERT_SERVICE_URL,
            'CHANNEL_SERVICE_URL': settings.CHANNEL_SERVICE_URL,
        }

        for name, url in services.items():
            if url:
                print(f"✅ {name}: {url}")
                tests_passed += 1
            else:
                print(f"❌ {name}: 未配置")
                tests_failed += 1

        # 测试数据库配置
        print(f"\n数据库配置:")
        print(f"   DATABASE_URL: {'已配置' if settings.DATABASE_URL else '未配置'}")

        # 测试Redis配置
        print(f"\nRedis配置:")
        print(f"   REDIS_URL: {'已配置' if settings.REDIS_URL else '未配置'}")

    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        tests_failed += 1

    print(f"\n配置测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_middleware():
    """测试中间件"""
    print("\n" + "="*60)
    print("测试 4: 中间件配置")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        from main import app

        # 获取中间件
        middleware = []
        for m in app.middleware_stack.middleware:
            middleware_class = m.__class__.__name__
            middleware.append(middleware_class)

        print(f"\n已配置的中间件数量: {len(middleware)}")
        for m in middleware:
            print(f"  - {m}")

        # 验证CORS中间件
        if any('CORSMiddleware' in m for m in middleware):
            print("✅ CORS 中间件已配置")
            tests_passed += 1
        else:
            print("❌ CORS 中间件未配置")
            tests_failed += 1

    except Exception as e:
        print(f"❌ 中间件测试失败: {e}")
        tests_failed += 1

    print(f"\n中间件测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("#" + " "*15 + "API Gateway 测试套件" + " "*16 + "#")
    print("#"*60)

    results = {
        "imports": test_imports(),
        "routes": test_routes(),
        "config": test_config(),
        "middleware": test_middleware(),
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
