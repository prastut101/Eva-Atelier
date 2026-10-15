import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.auth import get_db
from backend.app.database import Base
from backend.app.main import app
from backend.app.models.category import Category
from backend.app.models.product import Product
from backend.app.models.order import Order, OrderItem
from backend.app.models.user import User
import backend.app.routers.orders as orders_router


@pytest.fixture
def test_client(monkeypatch):
    # Each test gets an isolated in-memory SQLite database.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Mock Khalti: these tests must never contact the real payment API.
    def fake_initiate_payment(**kwargs):
        return {
            "pidx": "TEST-PIDX-12345",
            "payment_url": "https://example.com/mock-khalti-payment",
        }

    monkeypatch.setattr(
        orders_router,
        "initiate_payment",
        fake_initiate_payment,
    )

    with TestClient(app) as client:
        with TestingSessionLocal() as db:
            product = Product(
                name="Test Atelier Bag",
                description="A test product",
                price=1250.50,
                sku="TEST-BAG-001",
                in_stock=True,
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            product_id = product.id

            unavailable_product = Product(
                name="Unavailable Bag",
                description="Out of stock test product",
                price=900.00,
                sku="TEST-BAG-002",
                in_stock=False,
            )
            db.add(unavailable_product)
            db.commit()
            db.refresh(unavailable_product)
            unavailable_product_id = unavailable_product.id

        client.product_id = product_id
        client.unavailable_product_id = unavailable_product_id
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def checkout_payload(client, **overrides):
    payload = {
        "customer_name": "Test Customer",
        "customer_phone": "9800000000",
        "customer_email": "test@example.com",
        "shipping_address": "Test address, Dharan, Nepal",
        "notes": "Automated test order",
        "payment_method": "cod",
        "items": [
            {
                "product_id": client.product_id,
                "quantity": 2,
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_cod_checkout_creates_order_and_calculates_total(test_client):
    response = test_client.post(
        "/orders/checkout",
        json=checkout_payload(test_client),
    )

    assert response.status_code == 201
    body = response.json()

    assert body["payment_method"] == "cod"
    assert body["payment_status"] == "unpaid"
    assert body["subtotal"] == pytest.approx(2501.00)
    assert body["shipping_fee"] == pytest.approx(0.0)
    assert body["total"] == pytest.approx(2501.00)
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 2
    assert body["payment_url"] is None
    assert body["payment_error"] is None


def test_khalti_checkout_returns_payment_url_and_saves_reference(
    test_client,
):
    response = test_client.post(
        "/orders/checkout",
        json=checkout_payload(
            test_client,
            payment_method="khalti",
        ),
    )

    assert response.status_code == 201
    body = response.json()

    assert body["payment_method"] == "khalti"
    assert body["payment_status"] == "pending"
    assert body["payment_url"] == (
        "https://example.com/mock-khalti-payment"
    )
    assert body["payment_error"] is None

    with next(
        app.dependency_overrides[get_db]()
    ) as db:
        saved_order = db.query(Order).filter(
            Order.order_number == body["order_number"]
        ).one()

        assert saved_order.payment_reference == "TEST-PIDX-12345"


def test_checkout_rejects_nonexistent_product(test_client):
    response = test_client.post(
        "/orders/checkout",
        json=checkout_payload(
            test_client,
            items=[{"product_id": 999999, "quantity": 1}],
        ),
    )

    assert response.status_code == 400
    assert "no longer exist" in response.json()["detail"]


def test_checkout_rejects_out_of_stock_product(test_client):
    response = test_client.post(
        "/orders/checkout",
        json=checkout_payload(
            test_client,
            items=[
                {
                    "product_id": test_client.unavailable_product_id,
                    "quantity": 1,
                }
            ],
        ),
    )

    assert response.status_code == 409
    assert "unavailable" in response.json()["detail"]


def test_checkout_rejects_duplicate_product_ids(test_client):
    product_id = test_client.product_id

    response = test_client.post(
        "/orders/checkout",
        json=checkout_payload(
            test_client,
            items=[
                {"product_id": product_id, "quantity": 1},
                {"product_id": product_id, "quantity": 2},
            ],
        ),
    )

    assert response.status_code == 422
    assert "only once" in response.json()["detail"]


def test_checkout_rejects_invalid_payment_method(test_client):
    response = test_client.post(
        "/orders/checkout",
        json=checkout_payload(
            test_client,
            payment_method="bitcoin",
        ),
    )

    assert response.status_code == 422


def test_checkout_rejects_zero_quantity(test_client):
    response = test_client.post(
        "/orders/checkout",
        json=checkout_payload(
            test_client,
            items=[{"product_id": test_client.product_id, "quantity": 0}],
        ),
    )

    assert response.status_code == 422
