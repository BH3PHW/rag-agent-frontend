#!/usr/bin/env python3
"""
电商功能测试（简化版）
不依赖 tool_system，直接测试核心功能
"""
import sys
import re
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 简化测试：直接测试核心逻辑

ECOMMERCE_PLATFORMS = {
    "taobao": {"name": "淘宝/天猫", "enabled": True},
    "jd": {"name": "京东", "enabled": True},
    "douyin": {"name": "抖音商城", "enabled": True},
    "pinduoduo": {"name": "拼多多", "enabled": True},
    "xianyu": {"name": "闲鱼", "enabled": True},
    "xiaohongshu": {"name": "小红书", "enabled": True}
}

def _analyze_platform_from_message(message: str):
    """从用户消息中分析平台"""
    if not message:
        return None
    query_lower = message.lower()
    platform_keywords = {
        "taobao": ["淘宝", "taobao", "tb", "天猫", "ali"],
        "jd": ["京东", "jingdong", "jd"],
        "douyin": ["抖音", "douyin", "dy", "tiktok"],
        "pinduoduo": ["拼多多", "pinduoduo", "pdd"],
        "xianyu": ["闲鱼", "xianyu"],
        "xiaohongshu": ["小红书", "xiaohongshu", "xhs", "redbook"]
    }
    for platform, keywords in platform_keywords.items():
        if any(kw in query_lower for kw in keywords):
            return platform
    return None

def _extract_order_id_from_message(message: str):
    """从用户消息中提取订单号"""
    if not message:
        return None
    patterns = [
        r'([A-Z]{2,}-\d+)',           # ORD-123456
        r'(taobao_\d+)',              # taobao_123456
        r'(jd_\d+)',                  # jd_123456
        r'(JD\d+)',                    # JD123456789
        r'(DY\d+)',                   # DY202401150001
        r'(PDD\d+)',                  # PDD20240119001
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def consumer_identity_tool(user_message):
    """消费者身份识别"""
    detected_platform = _analyze_platform_from_message(user_message)
    order_id = _extract_order_id_from_message(user_message)
    identity_info = {
        "detected": detected_platform is not None,
        "platform": detected_platform,
        "platform_name": ECOMMERCE_PLATFORMS.get(detected_platform, {}).get("name") if detected_platform else None,
        "order_id_found": order_id,
    }
    if detected_platform:
        return {
            "success": True,
            "data": {
                "message": f"检测到您来自 {identity_info['platform_name']} 平台",
                "identity": identity_info,
            }
        }
    else:
        return {
            "success": True,
            "data": {
                "message": "无法自动识别您所在的平台",
                "identity": identity_info,
            }
        }

def test_consumer_identity():
    """测试消费者身份识别"""
    print("\n" + "="*60)
    print("测试 1: 消费者身份识别")
    print("="*60)
    
    test_cases = [
        ("我在淘宝买了东西，想查一下订单", "taobao"),
        ("京东的订单什么时候发货", "jd"),
        ("抖音买的零食收到没", "douyin"),
        ("拼多多上的商品怎么样", "pinduoduo"),
        ("查询一下我买的东西", None),
    ]
    
    passed = 0
    for message, expected in test_cases:
        result = consumer_identity_tool(message)
        detected = result.get("data", {}).get("identity", {}).get("platform")
        status = "✅" if detected == expected else "❌"
        if detected == expected:
            passed += 1
        print(f"\n{status} 消息: {message}")
        print(f"   检测到平台: {detected} (期望: {expected})")
        if result.get("success"):
            print(f"   返回: {result['data'].get('message')}")
    
    print(f"\n通过率: {passed}/{len(test_cases)}")
    return passed == len(test_cases)

def test_order_extraction():
    """测试订单号提取"""
    print("\n" + "="*60)
    print("测试 2: 订单号提取")
    print("="*60)
    
    test_cases = [
        ("查询订单 taobao_1001 的状态", "taobao_1001"),
        ("京东订单 JD1234567890 什么时候发货", "JD1234567890"),
        ("看一下 ORD-1002", "ORD-1002"),
        ("拼多多的 PDD20240119001 收到没", "PDD20240119001"),
    ]
    
    passed = 0
    for message, expected in test_cases:
        extracted = _extract_order_id_from_message(message)
        status = "✅" if extracted == expected else "❌"
        if extracted == expected:
            passed += 1
        print(f"\n{status} 消息: {message}")
        print(f"   提取订单号: {extracted} (期望: {expected})")
    
    print(f"\n通过率: {passed}/{len(test_cases)}")
    return passed == len(test_cases)

def test_platform_list():
    """测试平台列表"""
    print("\n" + "="*60)
    print("测试 3: 电商平台列表")
    print("="*60)
    
    print(f"\n支持的电商平台 ({len(ECOMMERCE_PLATFORMS)} 个):")
    for pid, p in ECOMMERCE_PLATFORMS.items():
        print(f"  - {pid}: {p['name']} {'✅' if p['enabled'] else '❌'}")
    
    return True

def test_integration():
    """测试完整流程"""
    print("\n" + "="*60)
    print("测试 4: 完整对话场景")
    print("="*60)
    
    scenarios = [
        {
            "user_message": "我在淘宝买了件衣服，订单号是 taobao_1001，什么时候发货？",
            "expected_platform": "taobao",
            "expected_order_id": "taobao_1001",
            "expected_action": "查询订单并返回物流信息"
        },
        {
            "user_message": "京东的 JD1234567890 到哪了？",
            "expected_platform": "jd",
            "expected_order_id": "JD1234567890",
            "expected_action": "查询物流轨迹"
        },
        {
            "user_message": "抖音订单什么时候发货",
            "expected_platform": "douyin",
            "expected_order_id": None,  # 没有指定订单号
            "expected_action": "先识别平台，提示用户提供订单号"
        },
    ]
    
    passed = 0
    for scenario in scenarios:
        platform = _analyze_platform_from_message(scenario["user_message"])
        order_id = _extract_order_id_from_message(scenario["user_message"])
        
        platform_ok = platform == scenario["expected_platform"]
        order_ok = order_id == scenario["expected_order_id"]
        
        status = "✅" if platform_ok and order_ok else "❌"
        if platform_ok and order_ok:
            passed += 1
            
        print(f"\n{status} 场景: {scenario['expected_action']}")
        print(f"   用户消息: {scenario['user_message']}")
        print(f"   识别平台: {platform} {'✅' if platform_ok else '❌'}")
        print(f"   提取订单: {order_id} {'✅' if order_ok else '❌'}")
    
    print(f"\n通过率: {passed}/{len(scenarios)}")
    return passed == len(scenarios)

def main():
    print("\n" + "="*60)
    print("电商功能测试")
    print("="*60)
    
    results = []
    results.append(("消费者身份识别", test_consumer_identity()))
    results.append(("订单号提取", test_order_extraction()))
    results.append(("平台列表", test_platform_list()))
    results.append(("完整场景", test_integration()))
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("="*60)

if __name__ == "__main__":
    main()
