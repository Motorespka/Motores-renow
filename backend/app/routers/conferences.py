from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import get_settings
from app.dependencies.auth import get_current_access
from app.integrations.supabase_rest import SupabaseRestClient
from app.schemas.conferences import (
    ConferenceDecisionRequest,
    ConferenceDecisionResponse,
    ConferenceDiffResponse,
    ConferenceListResponse,
    ConferenceRecord,
)
from app.services.access_service import AccessContext
from app.services.conferences_service import ConferencesService

router = APIRouter(prefix="/conferences", tags=["conferences"])


def _service() -> ConferencesService:
    settings = get_settings()
    gateway = SupabaseRestClient(settings)
    return ConferencesService(gateway)


@router.get("", response_model=ConferenceListResponse)
async def list_conferences(
    status_filter: str = Query(default="", alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    access: AccessContext = Depends(get_current_access),
) -> ConferenceListResponse:
    service = _service()
    data = await service.list(access, status=status_filter or "", limit=limit, offset=offset)
    items = [ConferenceRecord(**row) for row in (data.get("items") or [])]
    return ConferenceListResponse(total=int(data.get("total") or len(items)), items=items)


@router.post("/{motor_id}/diff", response_model=ConferenceDiffResponse)
async def generate_diff(
    motor_id: str,
    access: AccessContext = Depends(get_current_access),
) -> ConferenceDiffResponse:
    service = _service()
    row = await service.diff(access, motor_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao gerar diff.")
    return ConferenceDiffResponse(ok=True, record=ConferenceRecord(**row))


@router.post("/{motor_id}/decision", response_model=ConferenceDecisionResponse)
async def decide(
    motor_id: str,
    payload: ConferenceDecisionRequest,
    access: AccessContext = Depends(get_current_access),
) -> ConferenceDecisionResponse:
    service = _service()
    row = await service.decide(access, motor_id, approved=payload.approved, reason=payload.reason, notes=payload.notes)
    if not row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao salvar decisao.")
    return ConferenceDecisionResponse(ok=True, record=ConferenceRecord(**row))

