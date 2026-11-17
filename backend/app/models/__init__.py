"""集中导入所有模型，确保 SQLAlchemy metadata 注册完整。"""
from app.models.user import User  # noqa: F401
from app.models.category import AttributeTemplate, Category  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.blind_box import BlindBox  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.store import Store  # noqa: F401
from app.models.surplus_bag import SurplusBag  # noqa: F401
from app.models.carbon_record import CarbonRecord  # noqa: F401
from app.models.notification import Notification  # noqa: F401

__all__ = [
    "User",
    "Category",
    "AttributeTemplate",
    "Product",
    "BlindBox",
    "Order",
    "Store",
    "SurplusBag",
    "CarbonRecord",
    "Notification",
]
