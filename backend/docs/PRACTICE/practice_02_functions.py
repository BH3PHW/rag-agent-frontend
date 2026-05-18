# 练习02: 函数
# 运行: python practice_02_functions.py

print("=" * 40)
print("🎯 练习02: 函数")
print("=" * 40)

# 1. 简单函数
print("\n1. 简单函数:")
def greet(name):
    """问候函数"""
    return f"你好，{name}！"
print(greet("张三"))
print(greet("李四"))

# 2. 带返回值的函数
print("\n2. 带返回值的函数:")
def add(a, b):
    return a + b
result = add(5, 3)
print(f"5 + 3 = {result}")

# 3. 多个参数
print("\n3. 聊天函数:")
def chat_response(message):
    """简单的聊天回复"""
    responses = {
        "你好": "你好！我是智能客服",
        "帮助": "我可以帮你解答问题",
        "再见": "再见，有问题再来！"
    }
    return responses.get(message, "抱歉，我不太明白")

print(f" 问: 你好  -> 答: {chat_response('你好')}")
print(f" 问: 帮助  -> 答: {chat_response('帮助')}")
print(f" 问: 其他  -> 答: {chat_response('其他')}")

print("\n✅ 练习02完成！")
