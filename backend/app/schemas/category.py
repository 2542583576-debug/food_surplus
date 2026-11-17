from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    icon: str = ""
    sort_order: int = 0
    is_enabled: bool = True
    remark: str = Field(default="", max_length=255)


class CategoryCreate(CategoryBase):
    parent_id: int | None = None


class CategoryUpdate(BaseModel):
    """部分更新：只改传入的字段"""
    name: str | None = Field(default=None, min_length=1, max_length=50)
    icon: str | None = None
    sort_order: int | None = None
    is_enabled: bool | None = None
    remark: str | None = Field(default=None, max_length=255)


class CategoryMoveRequest(BaseModel):
    parent_id: int | None = None  # 移动到哪个父分类下（None=根）
    sort_order: int = 0


class CategoryOut(CategoryBase):
    id: int
    parent_id: int | None

    class Config:
        from_attributes = True


class CategoryTreeOut(CategoryOut):
    children: list["CategoryTreeOut"] = []


# ---------- 属性模板 ----------

class AttributeField(BaseModel):
    """模板中的单个属性定义"""
    key: str = Field(min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    label: str = Field(min_length=1, max_length=50)
    type: str = Field(pattern=r"^(text|number|select|multiselect|boolean)$")
    required: bool = False
    options: list[str] = []  # select/multiselect 的可选项


class AttributeTemplateCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=100)
    fields: list[AttributeField] = Field(min_length=1)


class AttributeTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    fields: list[AttributeField] | None = None


class AttributeTemplateOut(BaseModel):
    id: int
    category_id: int
    name: str
    fields: list[AttributeField]

    class Config:
        from_attributes = True
