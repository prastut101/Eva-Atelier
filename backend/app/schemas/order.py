from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class CheckoutItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=20)


class CheckoutCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    customer_phone: str = Field(min_length=7, max_length=30)
    customer_email: EmailStr | None = None
    shipping_address: str = Field(min_length=10, max_length=2000)
    notes: str | None = Field(default=None, max_length=1000)
    payment_method: Literal["cod", "khalti"] = "cod"
    items: list[CheckoutItem] = Field(min_length=1, max_length=50)

    @field_validator(
        "customer_name",
        "customer_phone",
        "shipping_address",
    )
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value


class OrderItemResponse(BaseModel):
    id: int
    product_id: int | None
    product_name: str
    product_sku: str
    unit_price: float
    quantity: int
    line_total: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_name: str
    customer_phone: str
    customer_email: str | None
    shipping_address: str
    notes: str | None
    subtotal: float
    shipping_fee: float
    total: float
    status: str
    payment_method: str
    payment_status: str
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class CheckoutResponse(OrderResponse):
    payment_url: str | None = None
    payment_error: str | None = None


class OrderStatusUpdate(BaseModel):
    status: Literal[
        "pending",
        "confirmed",
        "processing",
        "shipped",
        "delivered",
        "cancelled",
    ]


class PaymentStatusUpdate(BaseModel):
    payment_status: Literal[
        "unpaid",
        "pending",
        "paid",
        "failed",
        "refunded",
    ]
