from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_access
from app.schemas.access import AccessProfile, MeResponse
from app.services.access_service import AccessContext

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=MeResponse)
async def me(access: AccessContext = Depends(get_current_access)) -> MeResponse:
    profile = AccessProfile(
        user_id=access.user_id,
        email=access.email,
        username=access.username,
        nome=access.nome,
        display_name=access.display_name,
        role=access.role,
        plan=access.plan,
        ativo=access.ativo,
        is_admin=access.is_admin,
        cadastro_allowed=access.cadastro_allowed,
        tier=access.tier,
        source=access.source,
    )
    return MeResponse(authenticated=True, profile=profile)
