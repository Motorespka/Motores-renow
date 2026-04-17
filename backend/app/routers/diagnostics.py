from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import get_settings
from app.dependencies.auth import get_current_access
from app.integrations.supabase_rest import SupabaseRestClient
from app.schemas.diagnostics import (
    DiagnosticListResponse,
    DiagnosticRecord,
    DiagnosticRunRequest,
    DiagnosticRunResponse,
)
from app.services.access_service import AccessContext
from app.services.diagnostics_service import DiagnosticsService

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


def _service() -> DiagnosticsService:
    settings = get_settings()
    gateway = SupabaseRestClient(settings)
    return DiagnosticsService(gateway)


@router.get("", response_model=DiagnosticListResponse)
async def list_diagnostics(
    motor_id: str = Query(default="", description="Filtrar por motor_id"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    access: AccessContext = Depends(get_current_access),
) -> DiagnosticListResponse:
    service = _service()
    data = await service.list(access, motor_id=motor_id, limit=limit, offset=offset)
    items = [DiagnosticRecord(**row) for row in (data.get("items") or [])]
    return DiagnosticListResponse(total=int(data.get("total") or len(items)), items=items)


@router.get("/{diagnostic_id}", response_model=DiagnosticRecord)
async def get_diagnostic(
    diagnostic_id: str,
    access: AccessContext = Depends(get_current_access),
) -> DiagnosticRecord:
    service = _service()
    row = await service.get(access, diagnostic_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostico nao encontrado.")
    return DiagnosticRecord(**row)


@router.post("/run", response_model=DiagnosticRunResponse)
async def run_diagnostic(
    payload: DiagnosticRunRequest,
    access: AccessContext = Depends(get_current_access),
) -> DiagnosticRunResponse:
    service = _service()
    created = await service.run(access, motor_id=payload.motor_id or "", limit=payload.limit or 10)
    items = [DiagnosticRecord(**row) for row in (created or [])]
    return DiagnosticRunResponse(ok=True, message="Diagnostico gerado.", created=len(items), items=items)

