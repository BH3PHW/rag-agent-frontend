# 练习04: 简单聊天程序
# 运行: python practice_04_simple_chat.py

print("=" * 40)
print("🤖 练习04: 简单聊天程序")
print("=" * 40)

# 聊天数据存储
chat_history = []

# 聊天回复函数
def get_response(message):
    """获取机器人回复"""
    responses = {
        "你好": "你好！我是智能客服",
        "你叫什么": "我是智能客服",
        "帮助": "我可以帮你解答问题",
        "再见": "再见，有问题再来！"
    }
    return responses.get(message, "抱歉，我不太明白")

print("\n🤖 你好！我是智能客服，输入 'exit' 退出")
print("-" * 40)

while True:
    # 获取用户输入
    user_input = input("\n你: ").strip()
    
    if user_input.lower() == 'exit':
        print("🤖 再见！")
        break
    
    # 获取回复
    ai_response = get_response(user_input)
    print(f"🤖: {ai_response}")
    
    # 保存历史
    chat_history.append({
        "user": user_input,
        "ai": ai_response
    })

# 显示历史
if chat_history:
    print("\n" + "=" * 40)
    print("📋 聊天历史:")
    for i, chat in enumerate(chat_history):
        print(f"{i+1}. 你: {chat['user']}")
        print(f"   机器人: {chat['ai']}")

print("\n✅ 练习04完成！")
