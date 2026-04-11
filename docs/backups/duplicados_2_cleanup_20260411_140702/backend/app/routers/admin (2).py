from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import get_settings
from app.dependencies.auth import require_admin
from app.integrations.supabase_rest import SupabaseRestClient, SupabaseRestError
from app.schemas.admin import AdminUserSummary, AdminUserUpdatePayload, MessageResponse
from app.services.access_service import AccessContext
from app.services.admin_service import AdminService, AdminServiceUnavailableError

router = APIRouter(prefix="/admin", tags=["admin"])


def _service_unavailable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


def _admin_service() -> AdminService:
    settings = get_settings()
    gateway = SupabaseRestClient(settings)
    return AdminService(settings, gateway)


@router.get("/users/search", response_model=List[AdminUserSummary])
async def search_users(
    q: str = Query(default="", min_length=2),
    limit: int = Query(default=25, ge=1, le=50),
    _: AccessContext = Depends(require_admin),
) -> List[AdminUserSummary]:
    service = _admin_service()
    try:
        rows = await service.search_users(q, limit=limit)
    except AdminServiceUnavailableError as exc:
        raise _service_unavailable(str(exc))
    return [AdminUserSummary(**row) for row in rows]


@router.get("/users/{user_id}", response_model=AdminUserSummary)
async def get_user(
    user_id: str,
    _: AccessContext = Depends(require_admin),
) -> AdminUserSummary:
    service = _admin_service()
    try:
        row = await service.get_user(user_id)
    except AdminServiceUnavailableError as exc:
        raise _service_unavailable(str(exc))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
    return AdminUserSummary(**row)


@router.patch("/users/{user_id}", response_model=AdminUserSummary)
async def update_user(
    user_id: str,
    payload: AdminUserUpdatePayload,
    _: AccessContext = Depends(require_admin),
) -> AdminUserSummary:
    service = _admin_service()
    try:
        row = await service.update_user(user_id, payload.model_dump(exclude_unset=True))
    except AdminServiceUnavailableError as exc:
        raise _service_unavailable(str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except SupabaseRestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
    return AdminUserSummary(**row)


@router.get("/cadastro-access", response_model=List[Dict[str, Any]])
async def list_cadastro_access(_: AccessContext = Depends(require_admin)) -> List[Dict[str, Any]]:
    service = _admin_service()
    try:
        return await service.list_cadastro_access()
    except AdminServiceUnavailableError as exc:
        raise _service_unavailable(str(exc))


@router.post("/cadastro-access/{user_id}", response_model=MessageResponse)
async def grant_cadastro_access(
    user_id: str,
    access: AccessContext = Depends(require_admin),
) -> MessageResponse:
    service = _admin_service()
    try:
        await service.grant_cadastro_access(user_id=user_id, added_by=access.user_id)
    except AdminServiceUnavailableError as exc:
        raise _service_unavailable(str(exc))
    return MessageResponse(ok=True, message="Permissao de cadastro concedida.")


@router.delete("/cadastro-access/{user_id}", response_model=MessageResponse)
async def revoke_cadastro_access(
    user_id: str,
    _: AccessContext = Depends(require_admin),
) -> MessageResponse:
    service = _admin_service()
    try:
        await service.revoke_cadastro_access(user_id=user_id)
    except AdminServiceUnavailableError as exc:
        raise _service_unavailable(str(exc))
    return MessageResponse(ok=True, message="Permissao de cadastro removida.")
