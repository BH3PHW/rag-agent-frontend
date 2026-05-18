# 练习07: SQLite数据库
# 运行: python practice_07_sqlite.py

import sqlite3

print("=" * 40)
print("💾 练习07: SQLite数据库")
print("=" * 40)

# 1. 连接数据库
conn = sqlite3.connect('practice_faq.db')
cursor = conn.cursor()
print("\n1. 数据库连接成功！")

# 2. 创建FAQ表
cursor.execute('''
CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT,
    views INTEGER DEFAULT 0
)
''')
print("2. FAQ表创建成功！")

# 3. 插入示例数据
sample_data = [
    ("如何退货？", "请在订单页面申请退货", "售后"),
    ("配送时间？", "通常24小时内发货", "配送"),
    ("客服电话？", "400-123-4567", "客服")
]

# 先清空表，避免重复数据
cursor.execute("DELETE FROM faqs")
for q, a, c in sample_data:
    cursor.execute(
        "INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)",
        (q, a, c)
    )
conn.commit()
print("3. 示例数据插入成功！")

# 4. 查询所有FAQ
print("\n4. 查询所有FAQ:")
cursor.execute("SELECT * FROM faqs")
all_faqs = cursor.fetchall()
for faq in all_faqs:
    print(f"  [{faq[0]}] {faq[1]}")

# 5. 查询特定分类
category = "售后"
print(f"\n5. 查询 '{category}' 相关FAQ:")
cursor.execute("SELECT * FROM faqs WHERE category = ?", (category,))
service_faqs = cursor.fetchall()
for faq in service_faqs:
    print(f"  Q: {faq[1]}")
    print(f"  A: {faq[2]}")

# 6. 更新查看次数
faq_id = 1
cursor.execute("UPDATE faqs SET views = views + 1 WHERE id = ?", (faq_id,))
conn.commit()
print(f"\n6. FAQ ID {faq_id} 查看次数已更新")

# 7. 关闭连接
conn.close()
print("\n✅ 练习07完成！")
