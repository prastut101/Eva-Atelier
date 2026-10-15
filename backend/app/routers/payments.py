from html import escape

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.app.auth import get_db
from backend.app.models.order import Order
from backend.app.services.khalti import KhaltiError, lookup_payment

router = APIRouter()


def result_page(title: str, message: str) -> HTMLResponse:
    safe_title = escape(title)
    safe_message = escape(message)
    return HTMLResponse(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} | EVA Atelier</title>
  <style>
    body {{ margin: 0; padding: 2rem; background: #f8f5ef;
      color: #29251f; font: 16px/1.6 Arial, sans-serif; }}
    main {{ max-width: 560px; margin: 12vh auto; padding: 2rem;
      background: white; text-align: center; }}
    a {{ color: #29251f; }}
  </style>
</head>
<body><main>
  <h1>{safe_title}</h1>
  <p>{safe_message}</p>
  <a href="/">Return to EVA Atelier</a>
</main></body>
</html>"""
    )


@router.get("/khalti/callback", response_class=HTMLResponse)
def khalti_callback(
    pidx: str = Query(min_length=1, max_length=200),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(
        Order.payment_reference == pidx,
        Order.payment_method == "khalti",
    ).first()

    if order is None:
        return result_page(
            "Order not found",
            "We could not match this payment to an order. Please contact EVA Atelier.",
        )

    # A browser redirect is not proof of payment. Verify with Khalti.
    try:
        result = lookup_payment(pidx)
    except KhaltiError:
        return result_page(
            "Verification pending",
            "We could not verify your payment right now. Please contact EVA Atelier before attempting another payment.",
        )

    if result.get("pidx") != pidx:
        raise HTTPException(status_code=502, detail="Payment reference mismatch.")

    try:
        returned_amount = int(result.get("total_amount"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=502, detail="Invalid payment amount.")

    expected_amount = int(round(float(order.total) * 100))
    if returned_amount != expected_amount:
        raise HTTPException(status_code=502, detail="Payment amount mismatch.")

    payment_status = result.get("status")

    if payment_status == "Completed":
        order.payment_status = "paid"
        db.commit()
        return result_page(
            "Payment successful",
            f"Payment for order {order.order_number} has been verified.",
        )

    if order.payment_status != "paid":
        if payment_status == "Pending":
            order.payment_status = "pending"
            db.commit()
            return result_page(
                "Payment pending",
                f"Payment for order {order.order_number} has not been confirmed yet.",
            )

        order.payment_status = "failed"
        db.commit()

    return result_page(
        "Payment not completed",
        f"Payment for order {order.order_number} was not completed. If money was deducted, contact EVA Atelier before paying again.",
    )
