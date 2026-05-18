# 练习01: 你好世界
# 运行这个文件：python practice_01_hello.py

print("=" * 40)
print("🎯 练习01: 你好世界")
print("=" * 40)

# 1. 简单打印
print("\n1. 基础打印:")
print("你好，世界！")
print("欢迎学习RAG智能客服项目！")

# 2. 变量
name = "小明"
age = 25
course = "Python入门"
print(f"\n2. 变量:")
print(f"我是{name}，今年{age}岁，正在学习{course}")

# 3. 简单运算
a = 10
b = 20
print(f"\n3. 简单计算:")
print(f"{a} + {b} = {a + b}")
print(f"{a} * {b} = {a * b}")

# 4. 条件语句
print(f"\n4. 条件语句:")
if age >= 18:
    print(f"{name} 是成年人")
else:
    print(f"{name} 还没成年")

# 5. 循环
print(f"\n5. 循环:")
for i in range(5):
    print(f"  第{i}次: 你好！")

print("\n✅ 练习01完成！")
