from pathlib import Path

path = Path("backend/app/main.py")
source = path.read_text()

# Add the analytics router import.
anchor = "from backend.app.routers.orders import router as orders_router"
import_line = (
    "from backend.app.routers.analytics import router as analytics_router"
)

if import_line not in source:
    if anchor not in source:
        raise SystemExit(
            "Orders router import not found; no changes made."
        )
    source = source.replace(
        anchor,
        anchor + "\n" + import_line,
        1,
    )

# Register the analytics API router.
include_anchor = (
    'app.include_router(orders_router, prefix="/orders", tags=["Orders"])'
)
include_line = (
    'app.include_router(analytics_router, prefix="/admin/analytics", '
    'tags=["Admin Analytics"])'
)

if include_line not in source:
    if include_anchor not in source:
        raise SystemExit(
            "Orders router registration not found; no changes made."
        )
    source = source.replace(
        include_anchor,
        include_anchor + "\n" + include_line,
        1,
    )

# Add the analytics HTML page route.
route_anchor = '@app.get("/admin/orders", include_in_schema=False)'
route_block = (
    '@app.get("/admin/analytics", include_in_schema=False)\n'
    'def admin_analytics_page():\n'
    '    return FileResponse(FRONTEND_DIR / "admin" / "analytics.html")\n\n\n'
)

if 'def admin_analytics_page()' not in source:
    if route_anchor not in source:
        raise SystemExit(
            "Admin orders route not found; no changes made."
        )
    source = source.replace(
        route_anchor,
        route_block + route_anchor,
        1,
    )

path.write_text(source)
print("Analytics routes registered successfully.")
