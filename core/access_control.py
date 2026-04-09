from __future__ import annotations

import os
from typing import Any, Set

import streamlit as st
try:
    from supabase import create_client
except Exception:
    create_client = None

ADMIN_ROLES = {"admin", "owner", "superadmin", "root"}


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


def _upsert_profile_admin(role_value: str, is_admin: bool) -> None:
    profile = _current_profile()
    updated = False
    if is_admin and not _to_bool(profile.get("is_admin")):
        profile["is_admin"] = True
        updated = True
    if role_value and _to_text(profile.get("role")).lower() != role_value.lower():
        profile["role"] = role_value
        updated = True
    if updated:
        st.session_state["auth_user_profile"] = profile


def _read_secret_or_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return str(value).strip()
        try:
            secret_value = st.secrets.get(name)
            if secret_value:
                return str(secret_value).strip()
        except Exception:
            pass
    return ""


def _query_admin_with_client(client: Any, user_id: str, email: str) -> bool:
    if not client:
        return False

    attempts = []
    if user_id:
        attempts.append(("id", user_id, False))
    if email:
        attempts.append(("email", email, False))
        attempts.append(("email", email, True))

    for col, value, ilike in attempts:
        try:
            query = client.table("usuarios_app").select("role,ativo").limit(1)
            query = query.ilike(col, value) if ilike else query.eq(col, value)
            res = query.execute()
            row = (res.data or [None])[0]
            if not isinstance(row, dict):
                continue

            ativo = row.get("ativo")
            is_active = True if ativo is None else _to_bool(ativo)
            role = _to_text(row.get("role")).lower()
            is_admin = is_active and role in ADMIN_ROLES
            if role:
                _upsert_profile_admin(role, is_admin)
            if is_admin:
                return True
        except Exception:
            continue
    return False


def _is_admin_from_database(user_id: str, email: str) -> bool:
    cache_key = f"{user_id}|{email}"
    if st.session_state.get("_admin_cache_key") == cache_key:
        cached = st.session_state.get("_admin_cache_value")
        # Cache apenas positivo: evita ficar preso em "nao admin"
        # depois de uma promocao no banco (role -> admin).
        if cached is True:
            return True

    result = False

    client = st.session_state.get("_supabase_client")
    if client is not None and not getattr(client, "is_local_runtime", False):
        result = _query_admin_with_client(client, user_id=user_id, email=email)

    if not result and create_client is not None:
        url = _read_secret_or_env("SUPABASE_URL")
        service_key = _read_secret_or_env("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY")
        if url and service_key:
            try:
                svc = create_client(url, service_key)
                result = _query_admin_with_client(svc, user_id=user_id, email=email)
            except Exception:
                pass

    st.session_state["_admin_cache_key"] = cache_key
    if result:
        st.session_state["_admin_cache_value"] = True
    else:
        st.session_state.pop("_admin_cache_value", None)
    return bool(result)


def is_admin_user() -> bool:
    profile = _current_profile()

    if _to_bool(profile.get("is_admin")):
        return True

    if _to_bool(profile.get("admin")):
        return True

    role = _to_text(profile.get("role") or profile.get("perfil") or profile.get("tipo") or profile.get("admin")).lower()
    if role in ADMIN_ROLES:
        return True

    user_id = _to_text(st.session_state.get("auth_user_id"))
    email = _normalized_email(st.session_state.get("auth_user_email") or profile.get("email"))
    if user_id or email:
        if _is_admin_from_database(user_id=user_id, email=email):
            return True

    admin_ids = _allowlist("ADMIN_USER_IDS")
    admin_emails = {_normalized_email(v) for v in _allowlist("ADMIN_EMAILS")}

    single_email = _normalized_email(os.environ.get("ADMIN_EMAIL") or _get_secret("ADMIN_EMAIL"))
    if single_email:
        admin_emails.add(single_email)

    if user_id and user_id in admin_ids:
        return True
    if email and email in admin_emails:
        return True

    return False


def require_admin_access(feature_name: str) -> bool:
    if is_admin_user():
        return True
    st.error(f"Acesso restrito: apenas administrador pode usar '{feature_name}'.")
    st.info("Se esta conta deve ter permissao, configure admin/role/is_admin no perfil ou ADMIN_EMAILS/ADMIN_USER_IDS.")
    return False
