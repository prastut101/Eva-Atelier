from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.auth import get_current_admin, get_db
from backend.app.models.order import Order, OrderItem
from backend.app.models.user import User

router = APIRouter()


@router.get("/data")
def get_analytics(
    days: int = Query(default=30, ge=7, le=90),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    start_datetime = datetime.combine(
        start_date, datetime.min.time()
    )

    valid_orders = db.query(Order).filter(Order.status != "cancelled")
    paid_orders = valid_orders.filter(Order.payment_status == "paid")

    total_orders = db.query(func.count(Order.id)).scalar() or 0
    cancelled_orders = (
        db.query(func.count(Order.id))
        .filter(Order.status == "cancelled")
        .scalar() or 0
    )
    pending_orders = (
        db.query(func.count(Order.id))
        .filter(Order.status == "pending")
        .scalar() or 0
    )

    gross_order_value = (
        valid_orders.with_entities(
            func.coalesce(func.sum(Order.total), 0)
        ).scalar() or 0
    )
    paid_revenue = (
        paid_orders.with_entities(
            func.coalesce(func.sum(Order.total), 0)
        ).scalar() or 0
    )
    valid_count = valid_orders.count()
    average_order_value = (
        float(gross_order_value) / valid_count if valid_count else 0
    )

    date_expression = func.date(Order.created_at)
    trend_rows = (
        db.query(
            date_expression.label("day"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .filter(
            Order.created_at >= start_datetime,
            Order.status != "cancelled",
            Order.payment_status == "paid",
        )
        .group_by(date_expression)
        .order_by(date_expression)
        .all()
    )

    by_day = {
        str(row.day): {
            "orders": int(row.orders),
            "revenue": round(float(row.revenue or 0), 2),
        }
        for row in trend_rows
    }
    trend = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        values = by_day.get(day.isoformat(), {})
        trend.append({
            "date": day.isoformat(),
            "orders": values.get("orders", 0),
            "revenue": values.get("revenue", 0),
        })

    status_rows = (
        db.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )
    order_statuses = [
        {"status": str(name or "unknown"), "count": int(count)}
        for name, count in status_rows
    ]

    payment_rows = (
        db.query(
            Order.payment_method,
            Order.payment_status,
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0),
        )
        .group_by(Order.payment_method, Order.payment_status)
        .all()
    )
    payments = [
        {
            "method": str(method or "unknown"),
            "status": str(payment_status or "unknown"),
            "count": int(count),
            "amount": round(float(amount or 0), 2),
        }
        for method, payment_status, count, amount in payment_rows
    ]

    product_rows = (
        db.query(
            OrderItem.product_name,
            func.coalesce(func.sum(OrderItem.quantity), 0),
            func.coalesce(func.sum(OrderItem.line_total), 0),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status != "cancelled")
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(8)
        .all()
    )
    top_products = [
        {
            "name": str(name),
            "units_sold": int(units or 0),
            "sales_value": round(float(sales or 0), 2),
        }
        for name, units, sales in product_rows
    ]

    recent_orders = (
        db.query(Order)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .limit(8)
        .all()
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_days": days,
        "summary": {
            "total_orders": int(total_orders),
            "cancelled_orders": int(cancelled_orders),
            "pending_orders": int(pending_orders),
            "gross_order_value": round(float(gross_order_value), 2),
            "paid_revenue": round(float(paid_revenue), 2),
            "average_order_value": round(float(average_order_value), 2),
        },
        "trend": trend,
        "order_statuses": order_statuses,
        "payments": payments,
        "top_products": top_products,
        "recent_orders": [
            {
                "id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name,
                "total": round(float(order.total), 2),
                "status": order.status,
                "payment_status": order.payment_status,
                "created_at": (
                    order.created_at.isoformat()
                    if order.created_at else None
                ),
            }
            for order in recent_orders
        ],
    }
