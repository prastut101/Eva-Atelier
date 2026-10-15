import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE, override=True)


def _send_email(recipient: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
    sender = os.getenv("EMAIL_FROM") or username

    if not username or not password or not sender:
        raise RuntimeError("Email SMTP settings are incomplete.")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        server.send_message(message)


def send_order_confirmation(order) -> None:
    if not order.customer_email:
        return

    item_lines = [
        f"- {item.product_name} x {item.quantity}: NPR {item.line_total:,.2f}"
        for item in order.items
    ]

    body = (
        f"Dear {order.customer_name},\n\n"
        "Thank you for shopping with EVA Atelier.\n"
        "Your order has been received successfully.\n\n"
        f"Order number: {order.order_number}\n"
        f"Order status: {order.status}\n"
        f"Payment method: {order.payment_method.upper()}\n"
        f"Payment status: {order.payment_status}\n\n"
        "YOUR ORDER\n"
        + "\n".join(item_lines)
        + f"\n\nOrder total: NPR {order.total:,.2f}\n\n"
        "Please keep your order number for tracking.\n"
        "If you have questions, contact EVA Atelier.\n\n"
        "Every carry tells a story.\n"
        "EVA Atelier"
    )

    _send_email(
        order.customer_email,
        f"Order Confirmation {order.order_number} | EVA Atelier",
        body,
    )


def send_payment_success(order) -> None:
    if not order.customer_email:
        return

    body = (
        f"Dear {order.customer_name},\n\n"
        "Your Khalti payment has been verified successfully.\n\n"
        f"Order number: {order.order_number}\n"
        f"Amount paid: NPR {order.total:,.2f}\n"
        f"Order status: {order.status}\n\n"
        "Thank you for choosing EVA Atelier.\n\n"
        "Every carry tells a story.\n"
        "EVA Atelier"
    )

    _send_email(
        order.customer_email,
        f"Payment Confirmed {order.order_number} | EVA Atelier",
        body,
    )
