from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.routers import (
    admin,
    admin_demo_calculo,
    auth,
    cadastro,
    conferences,
    design,
    diagnostics,
    health,
    motors,
    settings as settings_router,
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(motors.router, prefix=settings.api_prefix)
app.include_router(cadastro.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(admin_demo_calculo.router, prefix=settings.api_prefix)
app.include_router(design.router, prefix=settings.api_prefix)
app.include_router(diagnostics.router, prefix=settings.api_prefix)
app.include_router(conferences.router, prefix=settings.api_prefix)
app.include_router(settings_router.router, prefix=settings.api_prefix)


def _frontend_base() -> str:
    return (settings.frontend_public_url or "http://localhost:3000").rstrip("/")


@app.get("/dashboard", include_in_schema=False)
async def redirect_browser_dashboard() -> RedirectResponse:
    """Quem abre a API na porta 8000 pensando que é o site cai aqui — envia para o Next.js."""
    return RedirectResponse(url=f"{_frontend_base()}/dashboard", status_code=307)


@app.get("/login", include_in_schema=False)
async def redirect_browser_login() -> RedirectResponse:
    return RedirectResponse(url=f"{_frontend_base()}/login", status_code=307)


@app.get("/")
async def root() -> dict:
    return {"ok": True, "name": settings.app_name, "prefix": settings.api_prefix}
