from __future__ import annotations

from dataclasses import dataclass
import re

from app.core.config import Settings
from app.integrations.supabase_rest import SupabaseRestClient

ADMIN_ROLES = {"admin", "owner", "superadmin", "root"}


@dataclass
class AccessContext:
    token: str
    user_id: str
    email: str
    username: str
    nome: str
    display_name: str
    role: str
    plan: str
    ativo: bool
    is_admin: bool
    cadastro_allowed: bool
    tier: str
    source: str

    @property
    def paid(self) -> bool:
        if self.is_admin:
            return True
        return (self.plan or "").lower() in {"paid", "pro", "premium", "enterprise", "business"}


class AccessService:
    def __init__(self, settings: Settings, gateway: SupabaseRestClient):
        self.settings = settings
        self.gateway = gateway

    async def resolve(self, token: str) -> AccessContext:
        user_payload = await self.gateway.auth_user(token)
        user_id = str(user_payload.get("id") or "").strip()
        email = str(user_payload.get("email") or "").strip().lower()
        if not user_id:
            raise ValueError("Token sem user_id.")

        profile = await self._fetch_profile(user_id=user_id, email=email, token=token)
        username = str((profile or {}).get("username") or "").strip()
        nome = str((profile or {}).get("nome") or "").strip()
        display_name = self._resolve_display_name(
            user_id=user_id,
            email=email,
            username=username,
            nome=nome,
        )
        role = str((profile or {}).get("role") or "").strip().lower()
        plan = str((profile or {}).get("plan") or "free").strip().lower() or "free"
        ativo_raw = (profile or {}).get("ativo")
        ativo = bool(ativo_raw) if isinstance(ativo_raw, bool) else str(ativo_raw).strip().lower() in {"1", "true", "yes", "sim"}

        is_admin = bool(profile) and ativo and role in ADMIN_ROLES
        if not is_admin:
            is_admin = self._is_admin_allowlist(user_id=user_id, email=email)

        has_paid_plan = plan in self.settings.paid_plans
        manual_cadastro = False
        if not is_admin and not has_paid_plan:
            manual_cadastro = await self._has_manual_cadastro_access(token=token, user_id=user_id)

        cadastro_allowed = bool(is_admin or has_paid_plan or manual_cadastro)
        if is_admin:
            tier = "admin"
        elif has_paid_plan:
            tier = "paid"
        elif manual_cadastro:
            tier = "cadastro"
        else:
            tier = "teaser"

        return AccessContext(
            token=token,
            user_id=user_id,
            email=email,
            username=username,
            nome=nome,
            display_name=display_name,
            role=role,
            plan=plan,
            ativo=ativo,
            is_admin=is_admin,
            cadastro_allowed=cadastro_allowed,
            tier=tier,
            source="usuarios_app" if profile else "none",
        )

    async def _fetch_profile(self, *, user_id: str, email: str, token: str) -> dict:
        by_id = await self.gateway.select_one(
            "usuarios_app",
            token=token,
            params={
                "select": "id,email,username,nome,role,plan,ativo",
                "id": f"eq.{user_id}",
            },
        )
        if by_id:
            return by_id

        if email:
            by_email = await self.gateway.select_one(
                "usuarios_app",
                token=token,
                params={
                    "select": "id,email,username,nome,role,plan,ativo",
                    "email": f"eq.{email}",
                },
            )
            if by_email:
                return by_email
        return {}

    def _is_admin_allowlist(self, *, user_id: str, email: str) -> bool:
        import os

        def _tokens(name: str) -> set[str]:
            raw = str(os.environ.get(name) or "").strip()
            if not raw:
                return set()
            return {p.strip().lower() for p in raw.replace(";", ",").split(",") if p.strip()}

        admin_ids = _tokens("ADMIN_USER_IDS")
        admin_emails = _tokens("ADMIN_EMAILS")
        single = str(os.environ.get("ADMIN_EMAIL") or "").strip().lower()
        if single:
            admin_emails.add(single)

        return user_id.lower() in admin_ids or email.lower() in admin_emails

    async def _has_manual_cadastro_access(self, *, token: str, user_id: str) -> bool:
        uid = str(user_id or "").strip()
        if not uid:
            return False

        params = {
            "select": "user_id",
            "user_id": f"eq.{uid}",
            "limit": "1",
        }
        try:
            rows = await self.gateway.select("cadastro_access", token=token, params=params)
            if rows:
                return True
        except Exception:
            pass

        if self.settings.supabase_service_role_key:
            try:
                rows = await self.gateway.select(
                    "cadastro_access",
                    use_service_role=True,
                    params=params,
                )
                if rows:
                    return True
            except Exception:
                pass

        return False

    @staticmethod
    def _humanize_identifier(value: str) -> str:
        txt = str(value or "").strip()
        if not txt:
            return ""
        txt = re.sub(r"_([0-9a-f]{8,})$", "", txt, flags=re.IGNORECASE)
        txt = txt.replace("_", " ").replace(".", " ").strip()
        if not txt:
            return ""
        return txt[:1].upper() + txt[1:]

    @classmethod
    def _resolve_display_name(cls, *, user_id: str, email: str, username: str, nome: str) -> str:
        if username:
            return username
        if nome:
            return nome
        local = email.split("@", 1)[0].strip() if "@" in email else ""
        if local:
            friendly = cls._humanize_identifier(local)
            if friendly:
                return friendly
        friendly_id = cls._humanize_identifier(user_id)
        if friendly_id:
            return friendly_id
        return "Usuario"
