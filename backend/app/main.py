from datetime import timedelta
from pathlib import Path
from backend.app.routers.payments import router as payments_router
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_db,
)
from backend.app.routers.orders import router as orders_router
from backend.app.routers.analytics import router as analytics_router
from backend.app.routers.categories import router as categories_router
from backend.app.routers.product_images import router as product_images_router
from backend.app.routers.products import router as products_router

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
UPLOADS_DIR = PROJECT_ROOT / "uploads"

app = FastAPI(
    title="EVA Atelier API",
    description="Backend API for the EVA Atelier store",
    version="1.0.0",
)

app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(
    product_images_router,
    prefix="/products",
    tags=["Product Images"],
)
app.include_router(categories_router, prefix="/categories", tags=["Categories"])
app.include_router(orders_router, prefix="/orders", tags=["Orders"])
app.include_router(analytics_router, prefix="/admin/analytics", tags=["Admin Analytics"])
app.include_router(payments_router, prefix="/payments", tags=["Payments"])

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR)),
    name="uploads",
)
app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR / "static")),
    name="static",
)


@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.username},
        expires_delta=expires,
    )

    return {"access_token": token, "token_type": "bearer"}


@app.get("/", include_in_schema=False)
def storefront():
    return FileResponse(FRONTEND_DIR / "templates" / "index.html")


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}


@app.get("/wishlist", include_in_schema=False)
def wishlist_page():
    return FileResponse(FRONTEND_DIR / "templates" / "wishlist.html")


@app.get("/track-order", include_in_schema=False)
def track_order_page():
    return FileResponse(FRONTEND_DIR / "templates" / "track-order.html")


@app.get("/product/{product_id}", include_in_schema=False)
def product_page(product_id: int, request: Request):
    return FileResponse(FRONTEND_DIR / "templates" / "product.html")


@app.get("/admin", include_in_schema=False)
def admin_page():
    return FileResponse(FRONTEND_DIR / "templates" / "admin.html")

@app.get("/admin/analytics", include_in_schema=False)
def admin_analytics_page():
    return FileResponse(FRONTEND_DIR / "admin" / "analytics.html")


@app.get("/admin/orders", include_in_schema=False)
def admin_orders_page():
    return FileResponse(FRONTEND_DIR / "admin" / "orders.html")
