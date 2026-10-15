from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.category import CategoryResponse


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=1, max_length=2000)
    price: float = Field(gt=0)
    in_stock: bool = True
    sku: str = Field(min_length=3, max_length=50)
    category_id: int | None = Field(default=None, gt=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    price: float | None = Field(default=None, gt=0)
    in_stock: bool | None = None
    sku: str | None = Field(default=None, min_length=3, max_length=50)
    category_id: int | None = Field(default=None, gt=0)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    in_stock: bool
    sku: str
    image_url: str | None = None
    category_id: int | None = None
    category: CategoryResponse | None = None

    model_config = ConfigDict(from_attributes=True)
