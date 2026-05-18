# 练习08: SQLAlchemy ORM
# 运行: python practice_08_orm.py

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

print("=" * 40)
print("🏗️ 练习08: SQLAlchemy ORM")
print("=" * 40)

# 1. 初始化
print("\n1. 初始化数据库连接...")
engine = create_engine('sqlite:///practice_orm_faq.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

# 2. 定义模型
class FAQ(Base):
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(200), nullable=False)
    answer = Column(String(500), nullable=False)
    category = Column(String(50), default="其他")
    views = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<FAQ(id={self.id}, question='{self.question}')>"

# 3. 创建表
Base.metadata.create_all(engine)
print("2. 数据库表创建成功！")

# 4. 使用会话
db = Session()

# 5. 添加数据
print("\n3. 添加示例FAQ...")
faq1 = FAQ(
    question="如何退货？",
    answer="请在订单页面申请退货，我们支持7天无理由退货",
    category="售后"
)
faq2 = FAQ(
    question="配送时间？",
    answer="通常24小时内发货，快递需要3-5天送达",
    category="配送"
)
faq3 = FAQ(
    question="客服工作时间？",
    answer="客服工作时间是每天9:00-18:00",
    category="客服"
)

db.add_all([faq1, faq2, faq3])
db.commit()
print("   添加成功！")

# 6. 查询所有数据
print("\n4. 查询所有FAQ:")
all_faqs = db.query(FAQ).all()
for faq in all_faqs:
    print(f"  [{faq.id}] {faq.question}")
    print(f"      答案: {faq.answer}")

# 7. 查询特定分类
print("\n5. 查询 '售后' 分类:")
service_faqs = db.query(FAQ).filter(FAQ.category == "售后").all()
for faq in service_faqs:
    print(f"  Q: {faq.question}")
    print(f"  A: {faq.answer}")

# 8. 更新数据
print("\n6. 更新FAQ查看次数...")
target_faq = db.query(FAQ).filter(FAQ.id == 1).first()
if target_faq:
    target_faq.views += 1
    db.commit()
    print(f"   FAQ '{target_faq.question}' 查看次数: {target_faq.views}")

# 9. 条件查询
print("\n7. 查询活跃FAQ:")
active_faqs = db.query(FAQ).filter(FAQ.active == True).all()
print(f"   共有 {len(active_faqs)} 条活跃FAQ")

# 10. 删除示例（注释掉，避免误删）
# print("\n8. 删除FAQ...")
# delete_faq = db.query(FAQ).filter(FAQ.id == 3).first()
# if delete_faq:
#     db.delete(delete_faq)
#     db.commit()
#     print(f"   已删除: {delete_faq.question}")

# 关闭会话
db.close()
print("\n✅ 练习08完成！")
