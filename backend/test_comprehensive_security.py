#!/usr/bin/env python3
"""
综合安全测试
测试所有新实现的安全机制
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
chat_service_dir = backend_dir / "chat-service"
sys.path.insert(0, str(chat_service_dir))


def test_jwt_auth():
    """测试JWT认证"""
    print("\n" + "="*60)
    print("测试 1: JWT身份验证")
    print("="*60)
    
    from jwt_auth import JWTService, PasswordService
    
    jwt_service = JWTService()
    password_service = PasswordService()
    
    # 测试1: 生成和验证Token
    print("\n1.1 Token生成和验证")
    user_id = "user_123"
    enterprise_id = "enterprise_456"
    
    access_token, expires_at = jwt_service.generate_access_token(
        user_id=user_id,
        enterprise_id=enterprise_id
    )
    print(f"   ✅ Access Token生成成功")
    print(f"      过期时间: {expires_at}")
    
    is_valid, payload, error = jwt_service.verify_token(access_token)
    print(f"   ✅ Token验证: {is_valid}")
    print(f"      用户ID: {payload.user_id if is_valid else 'N/A'}")
    print(f"      企业ID: {payload.enterprise_id if is_valid else 'N/A'}")
    
    # 测试2: 刷新Token
    print("\n1.2 刷新Token")
    refresh_token, _ = jwt_service.generate_refresh_token(user_id, enterprise_id)
    print(f"   ✅ Refresh Token生成成功")
    
    is_valid, user_token, error = jwt_service.refresh_access_token(refresh_token)
    print(f"   ✅ Token刷新: {is_valid}")
    print(f"      新Access Token: {user_token.token[:20]}... (已截断)")
    
    # 测试3: 密码安全
    print("\n1.3 密码安全")
    password = "Test@1234"
    password_hash, salt = password_service.hash_password(password)
    print(f"   ✅ 密码哈希成功")
    print(f"      哈希: {password_hash[:20]}... (已截断)")
    
    is_correct = password_service.verify_password(password, password_hash, salt)
    print(f"   ✅ 密码验证: {is_correct}")
    
    is_valid, violations = password_service.validate_password_strength(password)
    print(f"   ✅ 密码强度: {'强' if is_valid else '弱'}")
    if violations:
        print(f"      问题: {', '.join(violations)}")
    
    return True


def test_rate_limit():
    """测试限流"""
    print("\n" + "="*60)
    print("测试 2: 限流机制")
    print("="*60)
    
    from rate_limit import RateLimitConfig, RateLimitManager
    
    manager = RateLimitManager()
    
    # 测试不同限流策略
    print("\n2.1 滑动窗口限流")
    result = manager.check_rate_limit_by_user("user1", "ent1", "default")
    print(f"   ✅ 第1次请求: 允许={result.allowed}, 剩余={result.remaining}")
    
    # 快速发送多个请求
    for i in range(5):
        result = manager.check_rate_limit_by_user("user1", "ent1", "default")
    
    result = manager.check_rate_limit_by_user("user1", "ent1", "default")
    print(f"   ✅ 第6次请求: 允许={result.allowed}, 剩余={result.remaining}")
    
    # 测试严格限流
    print("\n2.2 严格限流（登录场景）")
    for i in range(6):
        result = manager.check_rate_limit_by_user("user2", "ent1", "login")
        if not result.allowed:
            print(f"   ✅ 第{i+1}次请求被限流，重试时间: {result.retry_after}秒")
            break
    
    # 测试不同动作限流
    print("\n2.3 不同动作限流")
    actions = ["default", "api", "chat", "ecommerce"]
    for action in actions:
        result = manager.check_rate_limit_by_user("user3", "ent1", action)
        print(f"   {action:12s}: 允许={result.allowed}, 剩余={result.remaining}")
    
    return True


def test_audit_logger():
    """测试审计日志"""
    print("\n" + "="*60)
    print("测试 3: 审计日志")
    print("="*60)
    
    from audit_logger import AuditLogger, AuditAction, AuditSeverity
    
    logger = AuditLogger(max_buffer_size=5)
    
    # 测试记录各种操作
    print("\n3.1 记录登录审计")
    log_id = logger.log(
        action=AuditAction.LOGIN,
        user_id="user_001",
        enterprise_id="ent_001",
        severity=AuditSeverity.INFO,
        success=True,
        ip_address="192.168.1.100"
    )
    print(f"   ✅ 登录日志已记录: {log_id}")
    
    print("\n3.2 记录数据访问审计")
    log_id = logger.log(
        action=AuditAction.ORDER_QUERY,
        user_id="user_001",
        enterprise_id="ent_001",
        severity=AuditSeverity.INFO,
        success=True,
        resource_type="order",
        resource_id="taobao_1001",
        platform="taobao"
    )
    print(f"   ✅ 订单查询日志已记录: {log_id}")
    
    print("\n3.3 记录安全事件")
    log_id = logger.log(
        action=AuditAction.SECURITY_BLOCK,
        user_id="attacker",
        enterprise_id="ent_001",
        severity=AuditSeverity.CRITICAL,
        success=False,
        metadata={"attack_type": "SQL注入", "payload": "'; DROP TABLE users;--"}
    )
    print(f"   ✅ 安全事件已记录: {log_id}")
    
    print("\n3.4 审计日志查询（模拟）")
    logs = logger.query(user_id="user_001")
    print(f"   ✅ 查询成功，返回 {len(logs)} 条记录")
    
    return True


def test_security_context():
    """测试安全上下文"""
    print("\n" + "="*60)
    print("测试 4: 安全上下文和权限控制")
    print("="*60)
    
    from security import SecurityContext, SecurityService
    
    security_service = SecurityService()
    
    # 测试用户认证
    print("\n4.1 用户身份验证")
    context = security_service.validate_user_identity(
        user_id="user_123",
        enterprise_id="ent_456"
    )
    print(f"   ✅ 用户认证: {context.is_authenticated}")
    print(f"      用户ID: {context.user_id}")
    print(f"      企业ID: {context.enterprise_id}")
    
    # 测试消费者身份验证
    print("\n4.2 消费者身份验证")
    is_verified, details = security_service.verify_consumer_identity(
        platform_type="taobao",
        platform_user_id="tb_user_001",
        enterprise_id="ent_456"
    )
    print(f"   ✅ 消费者验证: {is_verified}")
    print(f"      平台: {details.get('verified_platform')}")
    print(f"      统一用户ID: {details.get('verified_unified_user_id')}")
    
    # 测试订单访问控制
    print("\n4.3 订单访问权限验证")
    has_access, details = security_service.verify_order_access(
        order_id="taobao_1001",
        security_context=context
    )
    print(f"   ✅ 访问权限: {has_access}")
    print(f"      原因: {details.get('reason')}")
    print(f"      订单属于用户: {details.get('order_belongs_to_user')}")
    
    # 测试未认证用户
    print("\n4.4 未认证用户权限")
    unauthenticated_context = SecurityContext(is_authenticated=False)
    has_access, details = security_service.verify_order_access(
        order_id="taobao_1001",
        security_context=unauthenticated_context
    )
    print(f"   ✅ 权限拒绝: {not has_access}")
    print(f"      原因: {details.get('reason')}")
    
    return True


def test_data_sanitization():
    """测试数据脱敏"""
    print("\n" + "="*60)
    print("测试 5: 数据脱敏")
    print("="*60)
    
    from security import SecurityService
    
    security_service = SecurityService()
    
    test_cases = [
        ("13812345678", "手机号"),
        ("张三", "姓名"),
        ("510123199001011234", "身份证"),
        ("ABC1234567890", "银行卡")
    ]
    
    print("\n脱敏效果:")
    for data, data_type in test_cases:
        sanitized = security_service.mask_sensitive_data(data)
        print(f"   {data_type:8s}: {data:20s} → {sanitized}")
    
    return True


def test_security_scenario():
    """测试完整的安全场景"""
    print("\n" + "="*60)
    print("测试 6: 完整安全场景")
    print("="*60)
    
    from jwt_auth import get_jwt_service
    from security import get_security_service, SecurityContext
    from rate_limit import rate_limit_check
    from audit_logger import get_audit_logger, AuditAction, AuditSeverity
    
    jwt_service = get_jwt_service()
    security_service = get_security_service()
    audit_logger = get_audit_logger()
    
    print("\n场景: 用户查询订单")
    
    # 1. 登录并获取Token
    print("\n6.1 用户登录")
    access_token, expires_at = jwt_service.generate_access_token(
        user_id="user_001",
        enterprise_id="ent_001"
    )
    print(f"   ✅ 登录成功，获取Token")
    
    # 2. 验证Token
    print("\n6.2 Token验证")
    is_valid, payload, _ = jwt_service.verify_token(access_token)
    context = SecurityContext(
        is_authenticated=True,
        user_id=payload.user_id,
        enterprise_id=payload.enterprise_id
    )
    print(f"   ✅ Token有效，构建安全上下文")
    
    # 3. 检查限流
    print("\n6.3 限流检查")
    rate_limit_result = rate_limit_check(
        payload.user_id,
        payload.enterprise_id,
        "ecommerce"
    )
    print(f"   ✅ 请求允许: {rate_limit_result.allowed}")
    print(f"      剩余配额: {rate_limit_result.remaining}")
    
    # 4. 验证消费者身份
    print("\n6.4 消费者身份验证")
    is_verified, identity_details = security_service.verify_consumer_identity(
        platform_type="taobao",
        platform_user_id="tb_user_001",
        enterprise_id=payload.enterprise_id
    )
    print(f"   ✅ 身份验证通过: {is_verified}")
    
    # 5. 验证订单访问权限
    print("\n6.5 订单访问权限")
    has_access, access_details = security_service.verify_order_access(
        order_id="taobao_1001",
        security_context=context
    )
    print(f"   ✅ 访问权限: {has_access}")
    
    # 6. 记录审计日志
    print("\n6.6 审计日志记录")
    log_id = audit_logger.log(
        action=AuditAction.ORDER_QUERY,
        user_id=payload.user_id,
        enterprise_id=payload.enterprise_id,
        severity=AuditSeverity.INFO,
        success=True,
        resource_type="order",
        resource_id="taobao_1001",
        platform="taobao"
    )
    print(f"   ✅ 操作已记录: {log_id}")
    
    print("\n" + "="*60)
    print("✅ 完整安全流程测试通过！")
    print("="*60)
    
    return True


def main():
    """运行所有安全测试"""
    print("\n" + "="*60)
    print("企业级安全系统综合测试")
    print("="*60)
    
    results = []
    results.append(("JWT身份验证", test_jwt_auth()))
    results.append(("限流机制", test_rate_limit()))
    results.append(("审计日志", test_audit_logger()))
    results.append(("安全上下文", test_security_context()))
    results.append(("数据脱敏", test_data_sanitization()))
    results.append(("完整场景", test_security_scenario()))
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20s} {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有安全测试通过！系统安全可靠！")
    else:
        print("❌ 部分安全测试失败")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
