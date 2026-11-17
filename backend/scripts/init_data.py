"""初始化默认商家账号和示例分类（幂等：已存在则跳过）"""
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Category, User

DEFAULT_ADMIN = {"username": "admin", "password": "admin123", "shop_name": "示例门店"}

DEFAULT_CATEGORIES = [
    {"name": "面包", "sort_order": 1, "children": []},
    {"name": "水果", "sort_order": 2, "children": []},
    {"name": "甜品", "sort_order": 3, "children": []},
    {"name": "熟食", "sort_order": 4, "children": []},
]


def main():
    db = SessionLocal()
    try:
        # 默认账号
        user = db.scalar(select(User).where(User.username == DEFAULT_ADMIN["username"]))
        if user is None:
            db.add(User(
                username=DEFAULT_ADMIN["username"],
                password_hash=hash_password(DEFAULT_ADMIN["password"]),
                nickname="管理员",
                shop_name=DEFAULT_ADMIN["shop_name"],
            ))
            print(f"[init] 已创建默认账号 {DEFAULT_ADMIN['username']} / {DEFAULT_ADMIN['password']}")
        else:
            print("[init] 默认账号已存在，跳过")

        # 示例分类
        if db.scalar(select(Category).limit(1)) is None:
            for c in DEFAULT_CATEGORIES:
                db.add(Category(name=c["name"], sort_order=c["sort_order"]))
            print("[init] 已创建示例分类：面包/水果/甜品/熟食")
        else:
            print("[init] 分类已存在，跳过")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
