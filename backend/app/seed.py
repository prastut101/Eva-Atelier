from backend.app.database import SessionLocal
from backend.app.models.product import Product

sample_products = [
    {
        "name": "Luxury Tote Bag",
        "description": "An elegant everyday tote bag.",
        "price": 3500,
        "sku": "TOTE001",
        "image_url": "/static/images/Luxury%20Tote%20Bag.png",
        "in_stock": True,
    },
    {
        "name": "Elegant Shoulder Bag",
        "description": "A refined shoulder bag for everyday use.",
        "price": 4500,
        "sku": "SHOULDER001",
        "image_url": "/static/images/Elegant%20Shoulder%20Bag.png",
        "in_stock": True,
    },
    {
        "name": "Classic Crossbody Bag",
        "description": "A versatile classic crossbody bag.",
        "price": 4000,
        "sku": "CROSSBODY001",
        "image_url": "/static/images/Classic%20Crossbody%20Bag.png",
        "in_stock": True,
    },
    {
        "name": "Eva Classic Tote",
        "description": "A timeless tote from EVA Atelier.",
        "price": 3800,
        "sku": "EVA-TOTE-CLASSIC",
        "image_url": "/static/images/Eva%20Classic%20tote.png",
        "in_stock": True,
    },
    {
        "name": "Eva Classic Tote Premium",
        "description": "A premium tote from EVA Atelier.",
        "price": 5200,
        "sku": "EVA-TOTE-PREMIUM",
        "image_url": "/static/images/Eva%20classic%20tote%20premium.png",
        "in_stock": True,
    },
]

db = SessionLocal()

try:
    added_count = 0
    updated_count = 0

    for product_data in sample_products:
        product = (
            db.query(Product)
            .filter(Product.sku == product_data["sku"])
            .first()
        )

        if product is None:
            db.add(Product(**product_data))
            added_count += 1
        else:
            for field, value in product_data.items():
                setattr(product, field, value)
            updated_count += 1

    db.commit()
    print(f"Products added: {added_count}")
    print(f"Products updated: {updated_count}")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
