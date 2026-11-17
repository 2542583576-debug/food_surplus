from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AttributeTemplate(Base):
    """分类属性模板：定义该类商品需要填写哪些属性

    例如面包类：[{"key":"weight","label":"克重","type":"number","required":true}, ...]
    模板整体以 JSON 数组存在 attribute_schema 字段，商品按模板填值存 JSON。
    """

    __tablename__ = "attribute_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True, comment="挂载的分类"
    )
    name: Mapped[str] = mapped_column(String(100), comment="模板名称，如：面包类基础属性")
    attribute_schema: Mapped[str] = mapped_column(Text, comment="JSON 数组：属性定义列表")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    category: Mapped["Category"] = relationship(back_populates="attribute_templates")  # noqa: F821


class Category(Base):
    """树形分类（parent_id 自关联，邻接表模型）"""

    __tablename__ = "categories"
    __table_args__ = (Index("idx_parent_sort", "parent_id", "sort_order"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True, comment="父分类ID，根为NULL"
    )
    name: Mapped[str] = mapped_column(String(50), comment="分类名，如：面包/水果/甜品/熟食")
    icon: Mapped[str] = mapped_column(String(255), default="", comment="图标URL")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="同级排序，越小越靠前")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    remark: Mapped[str] = mapped_column(String(255), default="", comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    parent: Mapped["Category"] = relationship(remote_side="Category.id", backref="children")
    attribute_templates: Mapped[list["AttributeTemplate"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )
