import pytest
from pydantic import ValidationError

from backend.app.schemas.order import CheckoutCreate, CheckoutResponse


def valid_checkout(**overrides):
    data = {
        "customer_name": "Test Customer",
        "customer_phone": "9800000000",
        "customer_email": "test@example.com",
        "shipping_address": "Test address, Dharan, Nepal",
        "payment_method": "cod",
        "items": [{"product_id": 1, "quantity": 2}],
    }
    data.update(overrides)
    return data


def test_checkout_defaults_to_cash_on_delivery():
    checkout = CheckoutCreate(**valid_checkout())
    assert checkout.payment_method == "cod"


def test_checkout_accepts_khalti():
    checkout = CheckoutCreate(
        **valid_checkout(payment_method="khalti")
    )
    assert checkout.payment_method == "khalti"


def test_checkout_rejects_unknown_payment_method():
    with pytest.raises(ValidationError):
        CheckoutCreate(
            **valid_checkout(payment_method="unknown")
        )


def test_checkout_rejects_zero_quantity():
    with pytest.raises(ValidationError):
        CheckoutCreate(
            **valid_checkout(
                items=[{"product_id": 1, "quantity": 0}]
            )
        )


def test_checkout_response_has_payment_fields():
    assert "payment_url" in CheckoutResponse.model_fields
    assert "payment_error" in CheckoutResponse.model_fields
