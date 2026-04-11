from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import get_settings
from app.dependencies.auth import get_current_access
from app.integrations.supabase_rest import SupabaseRestClient
from app.schemas.motor import MotorDetailResponse, MotorListResponse, MotorRecord
from app.services.access_service import AccessContext
from app.services.motor_service import MotorService

router = APIRouter(prefix="/motors", tags=["motors"])


@router.get("", response_model=MotorListResponse)
async def list_motors(
    q: str = Query(default="", description="Busca textual"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    access: AccessContext = Depends(get_current_access),
) -> MotorListResponse:
    gateway = SupabaseRestClient(get_settings())
    service = MotorService(gateway)
    data = await service.list_motors(access, search=q, limit=limit, offset=offset)
    items = [MotorRecord(**row) for row in data["items"]]
    return MotorListResponse(mode=data["mode"], total=data["total"], items=items)


@router.get("/{motor_id}", response_model=MotorDetailResponse)
async def motor_detail(
    motor_id: str,
    access: AccessContext = Depends(get_current_access),
) -> MotorDetailResponse:
    gateway = SupabaseRestClient(get_settings())
    service = MotorService(gateway)
    row = await service.get_motor_detail(access, motor_id)
    if row is None:
        if not access.paid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Plano pago requerido para detalhe tecnico.",
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motor nao encontrado.")

    return MotorDetailResponse(item=MotorRecord(**row), raw=row)

