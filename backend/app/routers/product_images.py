from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from backend.app.auth import get_current_admin
from backend.app.database import SessionLocal
from backend.app.models.product import Product
from backend.app.models.user import User

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = PROJECT_ROOT / "uploads" / "products"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{product_id}/image")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    content = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Image must be 5 MB or smaller")

    try:
        with Image.open(BytesIO(content)) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Upload a valid JPEG, PNG, or WebP image",
        )

    if image_format not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WebP images are allowed",
        )

    filename = f"{uuid4().hex}{ALLOWED_FORMATS[image_format]}"
    destination = UPLOAD_DIR / filename
    image_url = f"/uploads/products/{filename}"

    try:
        destination.write_bytes(content)
        product.image_url = image_url
        db.commit()
        db.refresh(product)
    except Exception:
        db.rollback()
        if destination.exists():
            destination.unlink()
        raise HTTPException(
            status_code=500,
            detail="Could not save the product image",
        )

    return {
        "message": "Product image uploaded successfully",
        "product_id": product_id,
        "image_url": image_url,
    }
