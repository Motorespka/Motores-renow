from __future__ import annotations

from typing import Any, Dict

from app.integrations.supabase_rest import SupabaseRestClient
from app.services.access_service import AccessContext


class SettingsService:
    def __init__(self, gateway: SupabaseRestClient):
        self.gateway = gateway

    async def get_me(self, access: AccessContext) -> Dict[str, Any]:
        row = await self.gateway.select_one(
            "user_settings",
            token=access.token,
            params={"select": "user_id,ui_prefs,feature_flags", "user_id": f"eq.{access.user_id}"},
        )
        if row:
            return row
        # Create default row on first read (upsert by PK)
        rows = await self.gateway.upsert(
            "user_settings",
            token=access.token,
            payload={"user_id": access.user_id, "ui_prefs": {}, "feature_flags": {}},
            on_conflict="user_id",
        )
        return rows[0] if rows else {"user_id": access.user_id, "ui_prefs": {}, "feature_flags": {}}

    async def update_me(self, access: AccessContext, *, ui_prefs: Dict[str, Any] | None, feature_flags: Dict[str, Any] | None) -> Dict[str, Any]:
        current = await self.get_me(access)
        next_ui = dict(current.get("ui_prefs") or {})
        next_flags = dict(current.get("feature_flags") or {})
        if isinstance(ui_prefs, dict):
            next_ui.update(ui_prefs)
        if isinstance(feature_flags, dict):
            next_flags.update(feature_flags)
        rows = await self.gateway.upsert(
            "user_settings",
            token=access.token,
            payload={"user_id": access.user_id, "ui_prefs": next_ui, "feature_flags": next_flags},
            on_conflict="user_id",
        )
        return rows[0] if rows else {"user_id": access.user_id, "ui_prefs": next_ui, "feature_flags": next_flags}

