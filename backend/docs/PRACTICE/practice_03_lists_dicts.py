# 练习03: 列表和字典
# 运行: python practice_03_lists_dicts.py

print("=" * 40)
print("🎯 练习03: 列表和字典")
print("=" * 40)

# 1. 列表示例
print("\n1. 列表:")
faq_list = [
    "如何退货？",
    "配送时间？",
    "客服电话？"
]

print("FAQ列表:")
for i, faq in enumerate(faq_list):
    print(f"  {i+1}. {faq}")

# 添加新FAQ
faq_list.append("新的FAQ问题")
print(f"\n添加后列表长度: {len(faq_list)}")

# 2. 字典示例
print("\n2. 字典:")
faq_answers = {
    "如何退货？": "请在订单页面申请退货",
    "配送时间？": "通常24小时内发货",
    "客服电话？": "客服电话是400-123-4567"
}

# 查询FAQ
question = "如何退货？"
answer = faq_answers.get(question, "抱歉，没有找到答案")
print(f"问: {question}")
print(f"答: {answer}")

# 遍历字典
print("\n所有FAQ:")
for q, a in faq_answers.items():
    print(f" Q: {q}")
    print(f" A: {a}")
    print()

print("✅ 练习03完成！")
