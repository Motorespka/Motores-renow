from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.dependencies.auth import require_admin
from app.schemas.demo_calculo import (
    DemoCalculoSaveRequest,
    DemoCalculoSaveResponse,
    DemoCalculoStats,
    DemoCalculoSuggestRequest,
    DemoCalculoSuggestResponse,
    GeminiKeysStatusResponse,
)
from app.services.access_service import AccessContext
from app.services.oficial_calculo_service import OficialCalculoService

router = APIRouter(prefix="/admin/demo-calculo", tags=["admin-demo-calculo"])


def _service() -> OficialCalculoService:
    return OficialCalculoService()


def _index_missing(exc: FileNotFoundError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{exc}. Execute: python scripts/index_for_search.py",
    )


@router.get("/stats", response_model=DemoCalculoStats)
async def demo_stats(_: AccessContext = Depends(require_admin)) -> DemoCalculoStats:
    try:
        return DemoCalculoStats(**_service().stats())
    except FileNotFoundError as exc:
        raise _index_missing(exc)


@router.post("/suggest", response_model=DemoCalculoSuggestResponse)
async def demo_suggest(
    body: DemoCalculoSuggestRequest,
    _: AccessContext = Depends(require_admin),
) -> DemoCalculoSuggestResponse:
    try:
        data = _service().suggest(body.model_dump())
        return DemoCalculoSuggestResponse(**data)
    except FileNotFoundError as exc:
        raise _index_missing(exc)


@router.post("/save-oficial", response_model=DemoCalculoSaveResponse)
async def demo_save_oficial(
    body: DemoCalculoSaveRequest,
    _: AccessContext = Depends(require_admin),
) -> DemoCalculoSaveResponse:
    try:
        saved = _service().save_oficial(body.model_dump())
    except FileNotFoundError as exc:
        raise _index_missing(exc)
    return DemoCalculoSaveResponse(
        sha256_arquivo=saved["sha256_arquivo"],
        arquivo_rel=saved["arquivo_rel"],
        saved_at=saved["saved_at"],
        message="Calculo promovido ao manifesto OFICIAL e indice atualizado.",
    )


@router.get("/gemini-keys", response_model=GeminiKeysStatusResponse)
async def gemini_keys_status(_: AccessContext = Depends(require_admin)) -> GeminiKeysStatusResponse:
    try:
        from config.api_manager import get_gemini_api_manager

        summary = get_gemini_api_manager().status_summary()
        return GeminiKeysStatusResponse(**summary)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gemini API manager: {exc}",
        )
