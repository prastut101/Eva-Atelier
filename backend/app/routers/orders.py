import logging
import secrets
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.app.auth import get_current_admin, get_db
from backend.app.models.order import Order, OrderItem
from backend.app.models.product import Product
from backend.app.models.user import User
from backend.app.schemas.order import (
    CheckoutCreate,
    CheckoutResponse,
    OrderResponse,
    OrderStatusUpdate,
    PaymentStatusUpdate,
)
from backend.app.services.khalti import KhaltiError, initiate_payment
from backend.app.services.email import send_order_confirmation

router = APIRouter()
logger = logging.getLogger(__name__)


class CustomerOrderTrackRequest(BaseModel):
    order_number: str = Field(min_length=5, max_length=40)
    customer_phone: str = Field(min_length=7, max_length=30)


@router.post("/track")
def track_customer_order(
    data: CustomerOrderTrackRequest,
    db: Session = Depends(get_db),
):
    """Return limited tracking information after verifying checkout phone."""
    order_number = data.order_number.strip().upper()
    supplied_phone = "".join(ch for ch in data.customer_phone if ch.isdigit())

    order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.order_number == order_number)
        .first()
    )

    stored_phone = (
        "".join(ch for ch in order.customer_phone if ch.isdigit())
        if order else ""
    )

    # Use the same generic response for missing orders and mismatched phones.
    if (
        order is None
        or not supplied_phone
        or not stored_phone
        or not secrets.compare_digest(supplied_phone, stored_phone)
    ):
        raise HTTPException(
            status_code=404,
            detail="We couldn't verify that order. Check the order number and checkout phone number.",
        )

    return {
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "total": order.total,
        "items": [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "line_total": item.line_total,
            }
            for item in order.items
        ],
    }


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
)
def checkout(
    data: CheckoutCreate,
    db: Session = Depends(get_db),
):
    product_ids = [item.product_id for item in data.items]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=422,
            detail="Each product must appear only once in the cart.",
        )

    products = (
        db.query(Product)
        .filter(Product.id.in_(product_ids))
        .all()
    )
    product_map = {product.id: product for product in products}

    if len(product_map) != len(product_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more products no longer exist.",
        )

    subtotal = 0.0
    item_snapshots = []

    for requested_item in data.items:
        product = product_map[requested_item.product_id]

        if not product.in_stock:
            raise HTTPException(
                status_code=409,
                detail=f"{product.name} is currently unavailable.",
            )

        unit_price = round(float(product.price), 2)
        line_total = round(unit_price * requested_item.quantity, 2)
        subtotal = round(subtotal + line_total, 2)

        item_snapshots.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "product_sku": product.sku,
                "unit_price": unit_price,
                "quantity": requested_item.quantity,
                "line_total": line_total,
            }
        )

    # Shipping is free until a delivery fee is configured.
    shipping_fee = 0.0
    total = round(subtotal + shipping_fee, 2)

    order = Order(
        order_number=f"EVA-{secrets.token_hex(5).upper()}",
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        customer_email=(
            str(data.customer_email) if data.customer_email else None
        ),
        shipping_address=data.shipping_address,
        notes=data.notes,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total=total,
        status="pending",
        payment_method=data.payment_method,
        payment_status=(
            "pending" if data.payment_method == "khalti" else "unpaid"
        ),
    )

    try:
        order.items = [
            OrderItem(**snapshot) for snapshot in item_snapshots
        ]
        db.add(order)
        db.commit()
        db.refresh(order)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not create the order. Please try again.",
        )
    except Exception:
        db.rollback()
        raise

    saved_order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order.id)
        .one()
    )

    try:
        send_order_confirmation(saved_order)
    except Exception:
        logger.exception(
            "Failed to send order confirmation for %s",
            saved_order.order_number,
        )

    if saved_order.payment_method == "khalti":
        try:
            payment = initiate_payment(
                order_number=saved_order.order_number,
                amount_npr=float(saved_order.total),
                customer_name=saved_order.customer_name,
                customer_phone=saved_order.customer_phone,
                customer_email=saved_order.customer_email,
            )
        except KhaltiError:
            saved_order.payment_status = "failed"
            db.commit()

            return CheckoutResponse(
                **OrderResponse.model_validate(saved_order).model_dump(),
                payment_url=None,
                payment_error=(
                    "Your order was saved, but Khalti payment could not "
                    "be started. Contact EVA Atelier before placing "
                    "another order."
                ),
            )

        saved_order.payment_reference = payment["pidx"]
        saved_order.payment_status = "pending"

        try:
            db.commit()
            db.refresh(saved_order)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=(
                    "Payment was initiated, but the order's payment "
                    "reference could not be saved. Contact EVA Atelier "
                    "before attempting another payment."
                ),
            )

        return CheckoutResponse(
            **OrderResponse.model_validate(saved_order).model_dump(),
            payment_url=payment["payment_url"],
            payment_error=None,
        )

    return CheckoutResponse.model_validate(saved_order)


@router.get("/", response_model=list[OrderResponse])
def list_orders(
    limit: int = Query(default=50, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc(), Order.id.desc())
        .limit(limit)
        .all()
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "cancelled" and data.status != "cancelled":
        raise HTTPException(
            status_code=409,
            detail=(
                "A cancelled order cannot be reopened through this endpoint."
            ),
        )

    order.status = data.status
    db.commit()
    db.refresh(order)

    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order.id)
        .one()
    )


@router.patch("/{order_id}/payment-status", response_model=OrderResponse)
def update_payment_status(
    order_id: int,
    data: PaymentStatusUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    order.payment_status = data.payment_status
    db.commit()
    db.refresh(order)

    return (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.id == order.id)
        .one()
    )
