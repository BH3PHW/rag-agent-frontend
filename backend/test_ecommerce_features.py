#!/usr/bin/env python3
"""
电商功能集成测试
测试以下功能：
1. 消费者身份识别
2. 电商订单查询
3. 物流查询
4. 订单状态查询
"""
import sys
from pathlib import Path

# 设置路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

chat_service_dir = backend_dir / "chat-service"
sys.path.insert(0, str(chat_service_dir))


def test_consumer_identity():
    """测试消费者身份识别"""
    print("\n" + "="*60)
    print("测试 1: 消费者身份识别")
    print("="*60)
    
    import built_in_tools
    consumer_identity_tool = built_in_tools.consumer_identity_tool
    _analyze_platform_from_message = built_in_tools._analyze_platform_from_message
    
    test_cases = [
        ("我在淘宝买了东西，想查一下订单", "taobao"),
        ("京东的订单什么时候发货", "jd"),
        ("抖音买的零食收到没", "douyin"),
        ("拼多多上的商品怎么样", "pinduoduo"),
        ("查询一下我买的东西", None),  # 无法识别
    ]
    
    for message, expected in test_cases:
        result = consumer_identity_tool(user_message=message)
        detected = result.get("data", {}).get("identity", {}).get("platform")
        
        status = "✅" if detected == expected else "❌"
        print(f"\n{status} 消息: {message}")
        print(f"   检测到平台: {detected} (期望: {expected})")
        if result.get("success"):
            print(f"   返回消息: {result['data'].get('message')}")


def test_order_extraction():
    """测试订单号提取"""
    print("\n" + "="*60)
    print("测试 2: 订单号提取")
    print("="*60)
    
    import built_in_tools
    _extract_order_id_from_message = built_in_tools._extract_order_id_from_message
    
    test_cases = [
        ("查询订单 taobao_1001 的状态", "taobao_1001"),
        ("京东订单 JD1234567890 什么时候发货", "JD1234567890"),
        ("看一下 ORD-1002", "ORD-1002"),
        ("拼多多的 PDD20240119001 收到没", "PDD20240119001"),
    ]
    
    for message, expected in test_cases:
        extracted = _extract_order_id_from_message(message)
        status = "✅" if extracted == expected else "❌"
        print(f"\n{status} 消息: {message}")
        print(f"   提取订单号: {extracted} (期望: {expected})")


def test_ecommerce_order_query():
    """测试电商订单查询"""
    print("\n" + "="*60)
    print("测试 3: 电商订单查询")
    print("="*60)
    
    import built_in_tools
    ecommerce_order_tool = built_in_tools.ecommerce_order_tool
    
    test_cases = [
        {
            "message": "查询淘宝订单 taobao_1001",
            "expected_platform": "taobao",
            "expected_order": "taobao_1001"
        },
        {
            "message": "京东订单物流信息",
            "expected_platform": "jd",
            "expected_order": None  # 会使用默认订单
        },
        {
            "message": "我在抖音买的订单",
            "expected_platform": "douyin",
            "expected_order": None
        },
    ]
    
    for case in test_cases:
        result = ecommerce_order_tool(
            platform_type=None,  # 让工具自动识别
            order_id=None,       # 让工具自动提取
            user_message=case["message"]
        )
        
        detected_platform = result.get("data", {}).get("platform")
        detected_order = result.get("data", {}).get("order", {}).get("order_id")
        
        status = "✅" if detected_platform == case["expected_platform"] else "❌"
        print(f"\n{status} 消息: {case['message']}")
        print(f"   检测平台: {detected_platform} (期望: {case['expected_platform']})")
        
        if result.get("success"):
            order = result.get("data", {}).get("order")
            if order:
                print(f"   订单信息:")
                print(f"     - 订单号: {order.get('order_id')}")
                print(f"     - 商品: {order.get('product_name')}")
                print(f"     - 状态: {order.get('order_status')}")
                print(f"     - 金额: ¥{order.get('order_amount')}")
                if order.get('shipping_tracking_number'):
                    print(f"     - 快递: {order.get('shipping_carrier')} {order.get('shipping_tracking_number')}")
        else:
            print(f"   错误: {result.get('error')}")


def test_logistics_query():
    """测试物流查询"""
    print("\n" + "="*60)
    print("测试 4: 物流查询")
    print("="*60)
    
    import built_in_tools
    logistics_query_tool = built_in_tools.logistics_query_tool
    
    test_cases = [
        {
            "platform": "taobao",
            "order_id": "taobao_1001",
            "description": "淘宝已签收订单"
        },
        {
            "platform": "jd",
            "order_id": "jd_2001",
            "description": "京东配送中订单"
        },
    ]
    
    for case in test_cases:
        print(f"\n测试: {case['description']}")
        result = logistics_query_tool(
            platform_type=case["platform"],
            order_id=case["order_id"]
        )
        
        if result.get("success"):
            print(f"  ✅ 查询成功")
            print(f"     快递: {result.get('carrier')}")
            print(f"     单号: {result.get('tracking_number')}")
            print(f"     状态: {result.get('status')}")
            
            timeline = result.get("timeline", [])
            if timeline:
                print(f"     物流轨迹:")
                for item in timeline:
                    print(f"       - {item['time']}: {item['status']} ({item['location']})")
        else:
            print(f"  ❌ 查询失败: {result.get('error')}")


def test_platform_list():
    """测试平台列表"""
    print("\n" + "="*60)
    print("测试 5: 电商平台列表")
    print("="*60)
    
    import built_in_tools
    ecommerce_platforms_tool = built_in_tools.ecommerce_platforms_tool
    
    result = ecommerce_platforms_tool()
    
    if result.get("success"):
        platforms = result.get("data", {}).get("platforms", [])
        print(f"\n支持的电商平台 ({len(platforms)} 个):")
        for p in platforms:
            print(f"  - {p['id']}: {p['name']} {'✅' if p['enabled'] else '❌'}")
    else:
        print(f"❌ 查询失败: {result.get('error')}")


def main():
    print("\n" + "="*60)
    print("电商功能集成测试")
    print("="*60)
    
    try:
        test_consumer_identity()
        test_order_extraction()
        test_ecommerce_order_query()
        test_logistics_query()
        test_platform_list()
        
        print("\n" + "="*60)
        print("测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
