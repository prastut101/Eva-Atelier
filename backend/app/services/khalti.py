import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

KHALTI_BASE_URL = os.getenv(
    "KHALTI_BASE_URL",
    "https://dev.khalti.com/api/v2",
).rstrip("/")
KHALTI_SECRET_KEY = os.getenv("KHALTI_SECRET_KEY", "")
APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


class KhaltiError(Exception):
    """Raised when Khalti initiation or verification fails."""


def _headers() -> dict[str, str]:
    if not KHALTI_SECRET_KEY:
        raise KhaltiError("Khalti is not configured on the server.")

    return {
        "Authorization": f"Key {KHALTI_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def initiate_payment(
    *,
    order_number: str,
    amount_npr: float,
    customer_name: str,
    customer_phone: str,
    customer_email: str | None,
) -> dict:
    payload = {
        "return_url": f"{APP_BASE_URL}/payments/khalti/callback",
        "website_url": APP_BASE_URL,
        "amount": int(round(amount_npr * 100)),
        "purchase_order_id": order_number,
        "purchase_order_name": f"EVA Atelier order {order_number}",
        "customer_info": {
            "name": customer_name,
            "phone": customer_phone,
            **({"email": customer_email} if customer_email else {}),
        },
    }

    try:
        response = httpx.post(
            f"{KHALTI_BASE_URL}/epayment/initiate/",
            json=payload,
            headers=_headers(),
            timeout=20.0,
        )
        response.raise_for_status()
        result = response.json()
    except httpx.HTTPError as exc:
        raise KhaltiError("Could not initiate Khalti payment.") from exc
    except ValueError as exc:
        raise KhaltiError("Khalti returned an invalid response.") from exc

    if not result.get("pidx") or not result.get("payment_url"):
        raise KhaltiError("Khalti did not return a payment reference and URL.")

    return result


def lookup_payment(pidx: str) -> dict:
    try:
        response = httpx.post(
            f"{KHALTI_BASE_URL}/epayment/lookup/",
            json={"pidx": pidx},
            headers=_headers(),
            timeout=20.0,
        )
        response.raise_for_status()
        result = response.json()
    except httpx.HTTPError as exc:
        raise KhaltiError("Could not verify the Khalti transaction.") from exc
    except ValueError as exc:
        raise KhaltiError("Khalti returned an invalid verification response.") from exc

    return result
