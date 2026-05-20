#!/usr/bin/env python3
"""
安全功能测试
测试安全验证、消费者身份识别等功能
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
chat_service_dir = backend_dir / "chat-service"
sys.path.insert(0, str(chat_service_dir))

from security import SecurityService, SecurityContext, get_security_service
from ecommerce_integration import EcommerceIntegrationService


def test_security_context():
    """测试安全上下文"""
    print("\n" + "="*60)
    print("测试 1: 安全上下文")
    print("="*60)
    
    security_service = get_security_service()
    
    # 测试未认证的情况
    context1 = security_service.validate_user_identity(user_id=None, enterprise_id=None)
    print(f"未认证: authenticated={context1.is_authenticated}")
    
    # 测试认证的情况
    context2 = security_service.validate_user_identity(
        user_id="123e4567-e89b-12d3-a456-426614174000",
        enterprise_id="123e4567-e89b-12d3-a456-426614174001"
    )
    print(f"认证: authenticated={context2.is_authenticated}, user_id={context2.user_id}, enterprise_id={context2.enterprise_id}")
    
    return True


def test_consumer_identity_verification():
    """测试消费者身份验证"""
    print("\n" + "="*60)
    print("测试 2: 消费者身份验证")
    print("="*60)
    
    security_service = get_security_service()
    
    test_cases = [
        {
            "platform": "taobao",
            "user_id": "tb_user_001",
            "phone": "138****1234",
            "enterprise_id": "123e4567-e89b-12d3-a456-426614174001"
        },
        {
            "platform": "jd",
            "user_id": "jd_user_002",
            "phone": "139****5678",
            "enterprise_id": "123e4567-e89b-12d3-a456-426614174001"
        },
        {
            "platform": "douyin",
            "user_id": "dy_user_003",
            "phone": "137****9999",
            "enterprise_id": "123e4567-e89b-12d3-a456-426614174001"
        }
    ]
    
    all_passed = True
    for test in test_cases:
        is_verified, details = security_service.verify_consumer_identity(
            platform_type=test["platform"],
            platform_user_id=test["user_id"],
            phone=test["phone"],
            enterprise_id=test["enterprise_id"]
        )
        
        status = "✅ 通过" if is_verified else "❌ 失败"
        print(f"\n平台: {test['platform']}")
        print(f"  状态: {status}")
        print(f"  原因: {details.get('reason', 'N/A')}")
        print(f"  已验证平台: {details.get('verified_platform', 'N/A')}")
        print(f"  统一用户ID: {details.get('verified_unified_user_id', 'N/A')}")
        
        if not is_verified:
            all_passed = False
    
    return all_passed


def test_order_access_control():
    """测试订单访问控制"""
    print("\n" + "="*60)
    print("测试 3: 订单访问控制")
    print("="*60)
    
    security_service = get_security_service()
    
    # 创建认证的安全上下文
    authenticated_context = SecurityContext(
        is_authenticated=True,
        user_id="user_001",
        enterprise_id="123e4567-e89b-12d3-a456-426614174001",
        verified_platform="taobao",
        verified_platform_user_id="tb_user_001",
        unified_user_id="unified_user_001"
    )
    
    # 测试已认证用户访问订单
    has_access, details = security_service.verify_order_access(
        order_id="taobao_1001",
        security_context=authenticated_context
    )
    status = "✅ 通过" if has_access else "❌ 失败"
    print(f"\n已认证用户访问订单: {status}")
    print(f"  原因: {details.get('reason', 'N/A')}")
    print(f"  订单属于用户: {details.get('order_belongs_to_user', False)}")
    
    # 测试未认证用户
    unauthenticated_context = SecurityContext(is_authenticated=False)
    has_access, details = security_service.verify_order_access(
        order_id="taobao_1001",
        security_context=unauthenticated_context
    )
    status = "✅ 拒绝访问" if not has_access else "❌ 不应该允许访问"
    print(f"\n未认证用户访问订单: {status}")
    print(f"  原因: {details.get('reason', 'N/A')}")
    
    return True


def test_data_sanitization():
    """测试数据脱敏"""
    print("\n" + "="*60)
    print("测试 4: 数据脱敏")
    print("="*60)
    
    security_service = get_security_service()
    
    test_cases = [
        "13812345678",
        "张三",
        "510123199001011234"
    ]
    
    for data in test_cases:
        sanitized = security_service.mask_sensitive_data(data)
        print(f"原始: {data}")
        print(f"脱敏: {sanitized}\n")
    
    return True


def test_platform_analysis():
    """测试平台识别"""
    print("\n" + "="*60)
    print("测试 5: 平台识别")
    print("="*60)
    
    test_cases = [
        ("我在淘宝买了东西", "taobao"),
        ("京东的商品很便宜", "jd"),
        ("抖音直播下单", "douyin"),
        ("拼多多砍价", "pinduoduo"),
        ("闲鱼上淘了个二手", "xianyu"),
        ("小红书种草", "xiaohongshu"),
        ("我想买点东西", None)
    ]
    
    all_passed = True
    for message, expected_platform in test_cases:
        detected_platform = EcommerceIntegrationService.analyze_platform_from_query(message)
        
        status = "✅" if detected_platform == expected_platform else "❌"
        print(f"\n{status} 消息: {message}")
        print(f"   识别平台: {detected_platform}, 期望: {expected_platform}")
        
        if detected_platform != expected_platform:
            all_passed = False
    
    return all_passed


def main():
    """运行所有安全测试"""
    print("\n" + "="*60)
    print("电商系统安全测试")
    print("="*60)
    
    results = []
    results.append(("安全上下文", test_security_context()))
    results.append(("消费者身份验证", test_consumer_identity_verification()))
    results.append(("订单访问控制", test_order_access_control()))
    results.append(("数据脱敏", test_data_sanitization()))
    results.append(("平台识别", test_platform_analysis()))
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20s} {status}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有安全测试通过！")
    else:
        print("❌ 部分安全测试失败")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
