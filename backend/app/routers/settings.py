from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.dependencies.auth import get_current_access
from app.integrations.supabase_rest import SupabaseRestClient
from app.schemas.settings import MessageResponse, SettingsMeResponse, SettingsMeUpdateRequest
from app.services.access_service import AccessContext
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


def _service() -> SettingsService:
    settings = get_settings()
    gateway = SupabaseRestClient(settings)
    return SettingsService(gateway)


@router.get("/me", response_model=SettingsMeResponse)
async def get_me(access: AccessContext = Depends(get_current_access)) -> SettingsMeResponse:
    service = _service()
    row = await service.get_me(access)
    return SettingsMeResponse(ui_prefs=row.get("ui_prefs") or {}, feature_flags=row.get("feature_flags") or {})


@router.patch("/me", response_model=SettingsMeResponse)
async def update_me(
    payload: SettingsMeUpdateRequest,
    access: AccessContext = Depends(get_current_access),
) -> SettingsMeResponse:
    service = _service()
    row = await service.update_me(access, ui_prefs=payload.ui_prefs, feature_flags=payload.feature_flags)
    return SettingsMeResponse(ui_prefs=row.get("ui_prefs") or {}, feature_flags=row.get("feature_flags") or {})

