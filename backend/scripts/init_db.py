"""数据库初始化：建表 + 旧表补列 + 种子数据（全部幂等，可重复执行）。"""
import os

from sqlalchemy import text

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
import app.models  # noqa: F401  注册所有模型

# 兼容历史数据库中缺失的列
COMPAT_COLUMNS = {
    "users": [
        ("nickname", "VARCHAR(50) NOT NULL DEFAULT ''"),
        ("shop_name", "VARCHAR(100) NOT NULL DEFAULT ''"),
        ("role", "INT NOT NULL DEFAULT 0"),
        ("store_id", "INT NULL"),
        ("is_active", "TINYINT(1) NOT NULL DEFAULT 1"),
    ],
    "orders": [
        ("customer_name", "VARCHAR(50) NOT NULL DEFAULT ''"),
        ("merchant_id", "INT NULL"),
        ("pickup_date", "DATE NULL"),
        ("expire_time", "DATETIME NULL"),
        ("pay_method", "VARCHAR(20) NOT NULL DEFAULT 'online'"),
        ("pay_status", "INT NOT NULL DEFAULT 0"),
    ],
    "stores": [
        ("longitude", "DOUBLE NULL"),
        ("latitude", "DOUBLE NULL"),
    ],
}


def ensure_columns() -> None:
    with engine.begin() as conn:
        for table, columns in COMPAT_COLUMNS.items():
            exists = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema=:db AND table_name=:t"
                ),
                {"db": settings.MYSQL_DB, "t": table},
            ).scalar()
            if not exists:
                continue
            current = {
                row[0]
                for row in conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema=:db AND table_name=:t"
                    ),
                    {"db": settings.MYSQL_DB, "t": table},
                )
            }
            for name, ddl in columns:
                if name not in current:
                    conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{name}` {ddl}"))
                    print(f"[init] 已为 {table} 补列 {name}")


def seed() -> None:
    from app.models import Category, Store, SurplusBag, User

    db = SessionLocal()
    try:
        store = db.query(Store).first()
        if store is None:
            store = Store(
                store_name="惜食·阳光烘焙店（总店）",
                address="示例市示例区阳光路 1 号",
                phone="13800138000",
                cover="",
                business_hours="09:00-21:00",
                longitude=116.397128,
                latitude=39.916527,
                status=1,
            )
            db.add(store)
            db.flush()
            print("[init] 已创建示例门店")

        # 校正首店展示信息（历史旧数据）
        if store.store_name == "惜食示例门店":
            store.store_name = "惜食·阳光烘焙店（总店）"
            store.address = "示例市示例区阳光路 1 号"
            store.longitude = 116.397128
            store.latitude = 39.916527

        # 补充更多自提点，丰富门店地图（仅在门店数量过少时）
        if db.query(Store).count() < 3:
            db.add_all([
                Store(
                    store_name="惜食·鲜果轻食店",
                    address="示例市示例区绿园路 88 号",
                    phone="13800138001",
                    cover="",
                    business_hours="08:30-20:30",
                    longitude=116.410000,
                    latitude=39.925000,
                    status=1,
                ),
                Store(
                    store_name="惜食·社区便利点",
                    address="示例市示例区和平日街 12 号",
                    phone="13800138002",
                    cover="",
                    business_hours="10:00-22:00",
                    longitude=116.385000,
                    latitude=39.910000,
                    status=1,
                ),
            ])
            print("[init] 已创建更多自提点")

        admin = db.query(User).filter(User.username == "admin").first()
        admin_pwd = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
        if admin is None:
            db.add(
                User(
                    username="admin",
                    password_hash=hash_password(admin_pwd),
                    nickname="店长",
                    shop_name=store.store_name,
                    role=1,
                    store_id=store.id,
                    is_active=True,
                )
            )
            print(f"[init] 已创建管理员 admin / {admin_pwd}")
        else:
            changed = False
            if not str(admin.password_hash).startswith("$2"):
                admin.password_hash = hash_password(admin_pwd)
                changed = True
            if admin.role != 1:
                admin.role = 1
                changed = True
            if not admin.store_id:
                admin.store_id = store.id
                changed = True
            if changed:
                print("[init] 管理员账号信息已校正（密码/角色/绑定门店）")

        if db.query(User).filter(User.username == "user").first() is None:
            user_pwd = os.getenv("DEFAULT_USER_PASSWORD", "user123")
            db.add(
                User(
                    username="user",
                    password_hash=hash_password(user_pwd),
                    nickname="环保达人",
                    phone=None,
                    role=0,
                    is_active=True,
                )
            )
            print(f"[init] 已创建普通用户 user / {user_pwd}")

        if db.query(Category).count() == 0:
            for name, sort_order in (("面包", 1), ("水果", 2), ("甜品", 3), ("熟食", 4)):
                db.add(Category(name=name, sort_order=sort_order))
            print("[init] 已创建示例分类")

        if db.query(SurplusBag).count() == 0:
            db.add_all(
                [
                    SurplusBag(
                        store_id=store.id,
                        bag_name="傍晚面包惊喜袋",
                        cover="",
                        description="当日现烤面包余量，随机 3-5 件，低碳环保",
                        original_price=45.00,
                        sale_price=15.00,
                        stock=20,
                        pick_start_time="18:00",
                        pick_end_time="21:00",
                        status=1,
                    ),
                    SurplusBag(
                        store_id=store.id,
                        bag_name="鲜果轻食袋",
                        cover="",
                        description="当日新鲜水果与轻食组合，数量有限",
                        original_price=38.00,
                        sale_price=12.00,
                        stock=15,
                        pick_start_time="17:30",
                        pick_end_time="20:30",
                        status=1,
                    ),
                ]
            )
            print("[init] 已创建示例魔法袋")

        db.commit()
    finally:
        db.close()


def main() -> None:
    print(f"[init] 连接数据库: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}")
    Base.metadata.create_all(bind=engine)
    print(f"[init] 已注册数据表: {', '.join(sorted(Base.metadata.tables.keys()))}")
    try:
        ensure_columns()
    except Exception as exc:
        print(f"[init] 跳过补列（新表无需此步骤）: {exc}")
    seed()
    print("[init] 数据库初始化完成")


if __name__ == "__main__":
    main()
