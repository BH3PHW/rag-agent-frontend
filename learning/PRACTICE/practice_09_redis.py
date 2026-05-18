# 练习09: Redis缓存
# 运行前确保: pip install redis
# 运行: python practice_09_redis.py
# 注意: 需要Redis服务运行在 localhost:6379

import redis
import json
from datetime import timedelta

print("=" * 40)
print("⚡ 练习09: Redis缓存")
print("=" * 40)

try:
    # 1. 连接Redis
    print("\n1. 连接Redis...")
    r = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )
    # 测试连接
    r.ping()
    print("   连接成功！")
except Exception as e:
    print(f"   连接失败: {e}")
    print("   请确保Redis服务正在运行！")
    exit(1)

# 2. 简单键值对
print("\n2. 简单键值对:")
r.set('username', '小明')
r.set('age', 25)
print(f"   username: {r.get('username')}")
print(f"   age: {r.get('age')}")

# 3. 设置过期时间
print("\n3. 过期时间:")
r.setex('temp_code', timedelta(seconds=60), '123456')
print(f"   验证码: {r.get('temp_code')}")
print(f"   剩余时间: {r.ttl('temp_code')} 秒")

# 4. 列表操作
print("\n4. 列表操作:")
r.delete('chat_history')  # 清空旧数据
r.lpush('chat_history', '你好')
r.lpush('chat_history', '请问退货政策')
r.lpush('chat_history', '谢谢')
history = r.lrange('chat_history', 0, -1)
print(f"   聊天历史: {history}")
print(f"   最新消息: {r.lindex('chat_history', 0)}")

# 5. 哈希表
print("\n5. 哈希表:")
user_data = {
    'id': 'user_001',
    'name': '张三',
    'email': 'zhangsan@example.com',
    'role': 'customer'
}
r.hset('user:user_001', mapping=user_data)
print(f"   用户信息: {r.hgetall('user:user_001')}")
print(f"   用户姓名: {r.hget('user:user_001', 'name')}")

# 6. 计数器
print("\n6. 计数器:")
r.set('view_count', 0)
r.incr('view_count')
r.incr('view_count')
r.incrby('view_count', 5)
print(f"   查看次数: {r.get('view_count')}")

# 7. 存储JSON对象
print("\n7. JSON对象存储:")
session_data = {
    'session_id': 'sess_123',
    'user_id': 'user_001',
    'state': 'active',
    'last_message': '你好'
}
r.setex('session:sess_123', timedelta(hours=24), json.dumps(session_data))
loaded = json.loads(r.get('session:sess_123'))
print(f"   会话数据: {loaded}")

# 8. 简单缓存示例
print("\n8. FAQ缓存示例:")
def get_faq_answer(question: str) -> str:
    """获取FAQ答案，优先从缓存获取"""
    cache_key = f"faq:{question}"
    
    # 检查缓存
    cached = r.get(cache_key)
    if cached:
        print(f"   [缓存命中] {question}")
        return cached
    
    # 模拟从数据库查询
    faq_db = {
        "如何退货？": "请在订单页面申请退货",
        "配送时间？": "通常24小时内发货",
        "客服电话？": "400-123-4567"
    }
    answer = faq_db.get(question, "抱歉，没有找到答案")
    
    # 存入缓存，5分钟过期
    r.setex(cache_key, timedelta(minutes=5), answer)
    print(f"   [数据库查询] {question}")
    return answer

# 测试缓存
print(f"   第一次查询: {get_faq_answer('如何退货？')}")
print(f"   第二次查询: {get_faq_answer('如何退货？')}")

# 9. 清理演示数据（可选）
print("\n9. 清理演示数据...")
keys_to_delete = ['username', 'age', 'temp_code', 'chat_history', 
                  'user:user_001', 'view_count', 'session:sess_123']
for key in keys_to_delete:
    r.delete(key)
# 保留faq缓存用于演示

print("\n✅ 练习09完成！")
