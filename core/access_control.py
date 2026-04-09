from __future__ import annotations

import os
from typing import Any, Set

import streamlit as st

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
