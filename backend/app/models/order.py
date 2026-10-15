
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(40), unique=True, nullable=False, index=True)

    customer_name = Column(String(150), nullable=False)
    customer_phone = Column(String(30), nullable=False)
    customer_email = Column(String(254), nullable=True)
    shipping_address = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)

    subtotal = Column(Float, nullable=False)
    shipping_fee = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False)

    status = Column(String(30), nullable=False, default="pending")
    payment_method = Column(String(30), nullable=False, default="cod")
    payment_status = Column(String(30), nullable=False, default="unpaid")

    payment_reference = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )

    product_name = Column(String(150), nullable=False)
    product_sku = Column(String(50), nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    line_total = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
