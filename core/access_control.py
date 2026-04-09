from __future__ import annotations

import os
from typing import Any, Dict, Set

import streamlit as st

ADMIN_ROLES = {"admin", "owner", "superadmin", "root"}
DEFAULT_PLAN = "free"


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _to_text(value).lower()
    return text in {"1", "true", "yes", "sim", "admin"}


def _as_tokens(value: Any) -> Set[str]:
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        out = set()
        for item in value:
            token = _to_text(item)
            if token:
                out.add(token)
        return out
    raw = _to_text(value)
    if not raw:
        return set()
    normalized = raw.replace(";", ",").replace("\n", ",")
    return {part.strip() for part in normalized.split(",") if part.strip()}


def _normalized_email(value: Any) -> str:
    return _to_text(value).lower()


def _get_secret(name: str) -> Any:
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def _allowlist(name: str) -> Set[str]:
    env_values = _as_tokens(os.environ.get(name))
    secret_values = _as_tokens(_get_secret(name))
    return env_values | secret_values


def _current_profile() -> dict:
    profile = st.session_state.get("auth_user_profile")
    if isinstance(profile, dict):
        return profile
    return {}


def _get_supabase_client() -> Any:
    return st.session_state.get("_supabase_client")


def _get_authenticated_identity() -> tuple[str, str]:
    profile = _current_profile()
    user_id = _to_text(st.session_state.get("auth_user_id"))
    email = _normalized_email(st.session_state.get("auth_user_email") or profile.get("email"))

    client = _get_supabase_client()
    if (not user_id or not email) and client is not None and not getattr(client, "is_local_runtime", False):
        try:
            auth_user_res = client.auth.get_user()
            user = getattr(auth_user_res, "user", None)
            fetched_id = _to_text(getattr(user, "id", ""))
            fetched_email = _normalized_email(getattr(user, "email", ""))
            if fetched_id:
                user_id = fetched_id
                st.session_state["auth_user_id"] = fetched_id
            if fetched_email:
                email = fetched_email
                st.session_state["auth_user_email"] = fetched_email
        except Exception:
            pass

    return user_id, email


def _fetch_usuarios_app_profile(user_id: str) -> Dict[str, Any] | None:
    if not user_id:
        return None

    client = _get_supabase_client()
    if client is None or getattr(client, "is_local_runtime", False):
        return None

    try:
        res = (
            client
            .table("usuarios_app")
            .select("id,email,role,plan,ativo")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        row = (res.data or [None])[0]
        if isinstance(row, dict):
            return row
    except Exception:
        return None

    return None


def _merge_profile_cache(db_profile: Dict[str, Any] | None, email: str, is_admin: bool) -> None:
    merged = dict(_current_profile())
    if isinstance(db_profile, dict):
        merged.update(db_profile)
    if email and not _to_text(merged.get("email")):
        merged["email"] = email
    merged["is_admin"] = bool(is_admin)
    st.session_state["auth_user_profile"] = merged


def get_access_profile(force_refresh: bool = False) -> Dict[str, Any]:
    user_id, email = _get_authenticated_identity()
    cache_key = f"{user_id}|{email}"

    if not force_refresh and st.session_state.get("_access_cache_key") == cache_key:
        cached = st.session_state.get("_access_cache_value")
        if isinstance(cached, dict):
            return cached

    db_profile = _fetch_usuarios_app_profile(user_id)
    role = _to_text((db_profile or {}).get("role")).lower()
    plan = _to_text((db_profile or {}).get("plan")) or DEFAULT_PLAN
    ativo = _to_bool((db_profile or {}).get("ativo")) if db_profile else False

    # Fonte principal: usuarios_app (id + ativo + role)
    is_admin = bool(db_profile) and ativo and role == "admin"
    source = "usuarios_app" if db_profile else "none"

    # Fallback opcional por allowlist
    if not is_admin:
        admin_ids = _allowlist("ADMIN_USER_IDS")
        admin_emails = {_normalized_email(v) for v in _allowlist("ADMIN_EMAILS")}
        single_email = _normalized_email(os.environ.get("ADMIN_EMAIL") or _get_secret("ADMIN_EMAIL"))
        if single_email:
            admin_emails.add(single_email)

        if (user_id and user_id in admin_ids) or (email and email in admin_emails):
            is_admin = True
            source = "allowlist"

    _merge_profile_cache(db_profile, email=email, is_admin=is_admin)

    access = {
        "user_id": user_id,
        "email": email,
        "perfil_existe": bool(db_profile),
        "ativo": bool(ativo),
        "role": role,
        "plan": plan,
        "is_admin": bool(is_admin),
        "source": source,
    }

    st.session_state["_access_cache_key"] = cache_key
    st.session_state["_access_cache_value"] = access
    return access


def is_admin_user() -> bool:
    return bool(get_access_profile().get("is_admin"))


def require_admin_access(feature_name: str) -> bool:
    access = get_access_profile()
    if access.get("is_admin"):
        return True

    st.error(f"Acesso restrito: apenas administrador pode usar '{feature_name}'.")
    st.info("Regra de acesso: usuarios_app.id = auth.uid(), ativo = true e role = 'admin'.")
    return False
