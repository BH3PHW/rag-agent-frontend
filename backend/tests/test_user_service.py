"""
User Service 调试用例
======================

测试覆盖：
1. 导入测试 - 验证模块可以正确导入
2. 认证功能测试 - 密码哈希、JWT Token
3. 数据模型测试 - 用户、企业模型
4. API端点测试 - 验证路由配置
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
BACKEND_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR / "user-service"))


def test_imports():
    """测试User Service模块导入"""
    print("\n" + "="*60)
    print("测试 1: 模块导入")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    # 测试导入主模块
    try:
        from main import app, create_access_token, verify_password
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
        from models import User, Enterprise, SensitiveSettings, SemanticRule
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


def test_auth_functions():
    """测试认证功能"""
    print("\n" + "="*60)
    print("测试 2: 认证功能")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        from main import get_password_hash, verify_password, create_access_token, create_refresh_token, verify_token

        # 测试密码哈希
        print("\n[1] 测试密码哈希功能:")
        test_password = "test_password_123"
        hashed = get_password_hash(test_password)

        if hashed and len(hashed) > 0:
            print(f"✅ 密码哈希成功，长度: {len(hashed)}")
            tests_passed += 1
        else:
            print("❌ 密码哈希失败")
            tests_failed += 1

        # 测试密码验证
        print("\n[2] 测试密码验证功能:")
        if verify_password(test_password, hashed):
            print("✅ 密码验证成功")
            tests_passed += 1
        else:
            print("❌ 密码验证失败")
            tests_failed += 1

        # 测试错误密码验证
        if not verify_password("wrong_password", hashed):
            print("✅ 错误密码验证正确拒绝")
            tests_passed += 1
        else:
            print("❌ 错误密码验证异常")
            tests_failed += 1

        # 测试JWT Token创建
        print("\n[3] 测试JWT Token创建:")
        test_data = {
            "sub": "test_user_id",
            "enterprise_id": "test_enterprise_id"
        }

        access_token = create_access_token(test_data)
        refresh_token = create_refresh_token(test_data)

        if access_token and len(access_token) > 0:
            print(f"✅ Access Token 创建成功，长度: {len(access_token)}")
            tests_passed += 1
        else:
            print("❌ Access Token 创建失败")
            tests_failed += 1

        if refresh_token and len(refresh_token) > 0:
            print(f"✅ Refresh Token 创建成功，长度: {len(refresh_token)}")
            tests_passed += 1
        else:
            print("❌ Refresh Token 创建失败")
            tests_failed += 1

        # 测试Token验证
        print("\n[4] 测试JWT Token验证:")
        payload = verify_token(access_token)

        if payload and payload.get("sub") == "test_user_id":
            print("✅ Token 验证成功")
            print(f"   - 用户ID: {payload.get('sub')}")
            print(f"   - 企业ID: {payload.get('enterprise_id')}")
            tests_passed += 1
        else:
            print("❌ Token 验证失败")
            tests_failed += 1

    except Exception as e:
        print(f"❌ 认证功能测试失败: {e}")
        tests_failed += 1

    print(f"\n认证功能测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_data_models():
    """测试数据模型"""
    print("\n" + "="*60)
    print("测试 3: 数据模型")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        from models import User, Enterprise, SensitiveSettings, SemanticRule

        # 测试模型字段
        print("\n[1] User 模型:")
        print(f"   - id: {User.id}")
        print(f"   - username: {User.username}")
        print(f"   - email: {User.email}")
        print(f"   - enterprise_id: {User.enterprise_id}")
        tests_passed += 1

        print("\n[2] Enterprise 模型:")
        print(f"   - id: {Enterprise.id}")
        print(f"   - name: {Enterprise.name}")
        print(f"   - api_key: {Enterprise.api_key}")
        print(f"   - owner_id: {Enterprise.owner_id}")
        tests_passed += 1

        print("\n[3] SensitiveSettings 模型:")
        print(f"   - enterprise_id: {SensitiveSettings.enterprise_id}")
        print(f"   - enable_keyword_detection: {SensitiveSettings.enable_keyword_detection}")
        print(f"   - sensitive_words: {SensitiveSettings.sensitive_words}")
        tests_passed += 1

        print("\n[4] SemanticRule 模型:")
        print(f"   - enterprise_id: {SemanticRule.enterprise_id}")
        print(f"   - category: {SemanticRule.category}")
        print(f"   - keywords: {SemanticRule.keywords}")
        tests_passed += 1

    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        tests_failed += 1

    print(f"\n数据模型测试结果: ✅ {tests_passed} 通过, ❌ {tests_failed} 失败")
    return tests_failed == 0


def test_api_endpoints():
    """测试API端点"""
    print("\n" + "="*60)
    print("测试 4: API端点配置")
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
        auth_routes = [r for r in routes if '/auth/' in r[1]]
        enterprise_routes = [r for r in routes if '/enterprises' in r[1]]
        user_routes = [r for r in routes if '/users' in r[1]]

        print(f"\n总路由数: {len(routes)}")
        print(f"认证路由: {len(auth_routes)}")
        print(f"企业路由: {len(enterprise_routes)}")
        print(f"用户路由: {len(user_routes)}")

        # 验证关键路由
        critical_routes = [
            '/health',
            '/',
            '/api/v1/auth/login',
            '/api/v1/auth/register',
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


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("#" + " "*12 + "User Service 测试套件" + " "*18 + "#")
    print("#"*60)

    results = {
        "imports": test_imports(),
        "auth": test_auth_functions(),
        "models": test_data_models(),
        "endpoints": test_api_endpoints(),
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
