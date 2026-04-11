from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import Settings
from app.integrations.supabase_rest import SupabaseRestClient


class AdminServiceUnavailableError(RuntimeError):
    pass


class AdminService:
    def __init__(self, settings: Settings, gateway: SupabaseRestClient):
        self.settings = settings
        self.gateway = gateway

    def _service_enabled(self) -> bool:
        return bool(self.settings.supabase_service_role_key)

    def _ensure_service_role(self) -> None:
        if not self._service_enabled():
            raise AdminServiceUnavailableError(
                "SUPABASE_SERVICE_ROLE_KEY nao configurada no backend."
            )

    async def search_users(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        self._ensure_service_role()
        text = (query or "").strip()
        if len(text) < 2:
            return []

        rows = await self.gateway.select(
            "usuarios_app",
            use_service_role=True,
            params={
                "select": "id,email,username,nome,role,plan,ativo,created_at,updated_at",
                "or": SupabaseRestClient.build_or_ilike(["username", "nome", "email"], text),
                "limit": str(max(1, min(limit, 50))),
                "order": "created_at.desc",
            },
        )
        return rows

    async def get_user(self, user_id: str) -> Dict[str, Any] | None:
        self._ensure_service_role()
        uid = str(user_id or "").strip()
        if not uid:
            return None
        return await self.gateway.select_one(
            "usuarios_app",
            use_service_role=True,
            params={
                "select": "id,email,username,nome,role,plan,ativo,created_at,updated_at",
                "id": f"eq.{uid}",
            },
        )

    async def update_user(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        self._ensure_service_role()

        uid = str(user_id or "").strip()
        if not uid:
            return None

        allowed_fields = {"username", "nome", "role", "plan", "ativo"}
        safe_payload = {k: v for k, v in payload.items() if k in allowed_fields and v is not None}
        if not safe_payload:
            return await self.get_user(uid)

        if "role" in safe_payload:
            safe_payload["role"] = str(safe_payload["role"]).strip().lower()
        if "plan" in safe_payload:
            safe_payload["plan"] = str(safe_payload["plan"]).strip().lower()
        if "username" in safe_payload:
            safe_payload["username"] = str(safe_payload["username"]).strip().lower()

        if "role" in safe_payload and safe_payload["role"] not in {"user", "admin"}:
            raise ValueError("role invalida")
        if "plan" in safe_payload:
            valid_plans = set(self.settings.paid_plans) | {"free"}
            if safe_payload["plan"] not in valid_plans:
                raise ValueError("plan invalido")

        updated = await self.gateway.update(
            "usuarios_app",
            use_service_role=True,
            payload=safe_payload,
            filters={"id": f"eq.{uid}"},
        )
        return updated[0] if updated else await self.get_user(uid)

    async def list_cadastro_access(self, limit: int = 200) -> List[Dict[str, Any]]:
        self._ensure_service_role()
        return await self.gateway.select(
            "cadastro_access",
            use_service_role=True,
            params={
                "select": "user_id,added_by,created_at",
                "order": "created_at.desc",
                "limit": str(max(1, min(limit, 500))),
            },
        )

    async def grant_cadastro_access(self, user_id: str, added_by: str) -> List[Dict[str, Any]]:
        self._ensure_service_role()
        payload = {"user_id": user_id, "added_by": added_by}
        return await self.gateway.upsert(
            "cadastro_access",
            use_service_role=True,
            payload=payload,
            on_conflict="user_id",
        )

    async def revoke_cadastro_access(self, user_id: str) -> List[Dict[str, Any]]:
        self._ensure_service_role()
        return await self.gateway.delete(
            "cadastro_access",
            use_service_role=True,
            filters={"user_id": f"eq.{user_id}"},
        )
