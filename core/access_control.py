from __future__ import annotations

import os
import time
from typing import Any, Dict, Set

import streamlit as st

ADMIN_ROLES = {"admin", "owner", "superadmin", "root"}
DEFAULT_PLAN = "free"
CADASTRO_OPEN_FLAG = "CADASTRO_OPEN_TO_AUTHENTICATED"
APP_SETTINGS_TABLE = "app_settings"
CADASTRO_OPEN_SETTING_KEY = "cadastro_open_to_authenticated"
CADASTRO_OPEN_CACHE_KEY = "_cadastro_open_setting_cache"
CADASTRO_OPEN_CACHE_TTL_SECONDS = 15


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


def _set_cadastro_open_cache(value: bool) -> None:
    st.session_state[CADASTRO_OPEN_CACHE_KEY] = {
        "value": bool(value),
        "ts": float(time.time()),
    }


def _get_cached_cadastro_open() -> bool | None:
    cached = st.session_state.get(CADASTRO_OPEN_CACHE_KEY)
    if not isinstance(cached, dict):
        return None
    ts = float(cached.get("ts") or 0.0)
    if (time.time() - ts) > CADASTRO_OPEN_CACHE_TTL_SECONDS:
        return None
    return bool(cached.get("value"))


def _fetch_cadastro_open_from_db(client: Any | None = None) -> bool:
    resolved_client = _resolve_supabase_client(client)
    if resolved_client is None or getattr(resolved_client, "is_local_runtime", False):
        return False

    try:
        res = (
            resolved_client
            .table(APP_SETTINGS_TABLE)
            .select("key,value_bool")
            .eq("key", CADASTRO_OPEN_SETTING_KEY)
            .limit(1)
            .execute()
        )
        rows = getattr(res, "data", None) or []
        if not rows:
            return False
        row = rows[0] if isinstance(rows[0], dict) else {}
        if "value_bool" in row and row.get("value_bool") is not None:
            return bool(row.get("value_bool"))
    except Exception:
        return False

    return False


def _current_profile() -> dict:
    profile = st.session_state.get("auth_user_profile")
    if isinstance(profile, dict):
        return profile
    return {}


def _get_supabase_client() -> Any:
    return st.session_state.get("_supabase_client")


def _resolve_supabase_client(client: Any | None = None) -> Any:
    if client is not None:
        return client
    return _get_supabase_client()


def _get_authenticated_identity(client: Any | None = None) -> tuple[str, str]:
    profile = _current_profile()
    user_id = _to_text(st.session_state.get("auth_user_id"))
    email = _normalized_email(st.session_state.get("auth_user_email") or profile.get("email"))

    client = _resolve_supabase_client(client)
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


def _partial_url(url: str) -> str:
    txt = (url or "").strip()
    if not txt:
        return ""
    if "://" in txt:
        head, tail = txt.split("://", 1)
        return f"{head}://{tail[:18]}..."
    return f"{txt[:24]}..."


def _query_debug_payload(table: str, method: str, field: str, value: str) -> Dict[str, Any]:
    return {
        "table": table,
        "method": method,
        "field": field,
        "value": value,
        "status": "pending",
        "row_count": 0,
        "data": None,
        "error": None,
    }


def _fetch_usuarios_app_profile(user_id: str, email: str, client: Any | None = None) -> Dict[str, Any] | None:
    email_norm = _normalized_email(email)
    client = _resolve_supabase_client(client)

    supabase_url = ""
    try:
        supabase_url = str(st.secrets.get("SUPABASE_URL") or "")
    except Exception:
        supabase_url = ""
    if not supabase_url:
        supabase_url = str(os.environ.get("SUPABASE_URL") or "")

    debug = {
        "table": "usuarios_app",
        "supabase_url_partial": _partial_url(supabase_url),
        "is_local_runtime": bool(getattr(client, "is_local_runtime", False)) if client is not None else False,
        "user_id": user_id,
        "email": email_norm,
        "source": "none",
        "by_id": _query_debug_payload("usuarios_app", "eq", "id", user_id),
        "by_email": _query_debug_payload("usuarios_app", "eq", "email", email_norm),
        "by_email_ilike": _query_debug_payload("usuarios_app", "ilike", "email", email_norm),
    }

    st.session_state["_access_profile_debug"] = debug

    if client is None or getattr(client, "is_local_runtime", False):
        debug["reason"] = "client_unavailable_or_local_runtime"
        st.session_state["_access_profile_debug"] = debug
        return None

    perfil = None

    if user_id:
        try:
            res = (
                client
                .table("usuarios_app")
                .select("id,email,role,plan,ativo")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", None) or []
            debug["by_id"]["status"] = "success"
            debug["by_id"]["row_count"] = len(rows)
            debug["by_id"]["data"] = rows[0] if rows else None
            if rows:
                perfil = rows[0]
                debug["source"] = "id"
        except Exception as exc:
            debug["by_id"]["status"] = "error"
            debug["by_id"]["error"] = str(exc)

    if not perfil and email_norm:
        try:
            res = (
                client
                .table("usuarios_app")
                .select("id,email,role,plan,ativo")
                .eq("email", email_norm)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", None) or []
            debug["by_email"]["status"] = "success"
            debug["by_email"]["row_count"] = len(rows)
            debug["by_email"]["data"] = rows[0] if rows else None
            if rows:
                perfil = rows[0]
                debug["source"] = "email"
        except Exception as exc:
            debug["by_email"]["status"] = "error"
            debug["by_email"]["error"] = str(exc)

    if not perfil and email_norm:
        try:
            res = (
                client
                .table("usuarios_app")
                .select("id,email,role,plan,ativo")
                .ilike("email", email_norm)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", None) or []
            debug["by_email_ilike"]["status"] = "success"
            debug["by_email_ilike"]["row_count"] = len(rows)
            debug["by_email_ilike"]["data"] = rows[0] if rows else None
            if rows:
                perfil = rows[0]
                debug["source"] = "email_ilike"
        except Exception as exc:
            debug["by_email_ilike"]["status"] = "error"
            debug["by_email_ilike"]["error"] = str(exc)

    st.session_state["_access_profile_debug"] = debug
    if isinstance(perfil, dict):
        perfil["_source"] = debug.get("source", "none")
    return perfil


def _merge_profile_cache(db_profile: Dict[str, Any] | None, email: str, is_admin: bool) -> None:
    merged = dict(_current_profile())
    if isinstance(db_profile, dict):
        merged.update(db_profile)
    if email and not _to_text(merged.get("email")):
        merged["email"] = email
    merged["is_admin"] = bool(is_admin)
    st.session_state["auth_user_profile"] = merged


def get_access_profile(client: Any | None = None, force_refresh: bool = False) -> Dict[str, Any]:
    resolved_client = _resolve_supabase_client(client)
    user_id, email = _get_authenticated_identity(resolved_client)
    auth_flag = bool(st.session_state.get("auth_is_authenticated"))
    authenticated = bool(user_id) and (auth_flag or bool(email))
    cache_key = f"{user_id}|{email}|{int(authenticated)}"

    if not force_refresh and st.session_state.get("_access_cache_key") == cache_key:
        cached = st.session_state.get("_access_cache_value")
        if isinstance(cached, dict):
            return cached

    db_profile = _fetch_usuarios_app_profile(user_id, email, resolved_client)
    role = _to_text((db_profile or {}).get("role")).lower()
    plan = _to_text((db_profile or {}).get("plan")) or DEFAULT_PLAN
    ativo = _to_bool((db_profile or {}).get("ativo")) if db_profile else False

    # Fonte principal: usuarios_app (id + ativo + role)
    is_admin = authenticated and bool(db_profile) and ativo and role in ADMIN_ROLES
    source = "usuarios_app" if db_profile else "none"

    # Fallback opcional por allowlist
    if authenticated and not is_admin:
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
        "authenticated": authenticated,
        "user_id": user_id,
        "email": email,
        "perfil_existe": bool(db_profile),
        "profile_source": _to_text((db_profile or {}).get("_source")),
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


def get_cadastro_open_setting(client: Any | None = None, force_refresh: bool = False) -> bool:
    # Override opcional por secret/env (util para emergencias).
    forced_open = _to_bool(os.environ.get(CADASTRO_OPEN_FLAG) or _get_secret(CADASTRO_OPEN_FLAG))
    if forced_open:
        _set_cadastro_open_cache(True)
        return True

    if not force_refresh:
        cached = _get_cached_cadastro_open()
        if cached is not None:
            return cached

    db_value = _fetch_cadastro_open_from_db(client=client)
    _set_cadastro_open_cache(db_value)
    return db_value


def set_cadastro_open_setting(enabled: bool, client: Any | None = None) -> tuple[bool, str]:
    resolved_client = _resolve_supabase_client(client)
    if resolved_client is None:
        return False, "Cliente Supabase indisponivel."

    if getattr(resolved_client, "is_local_runtime", False):
        _set_cadastro_open_cache(bool(enabled))
        return True, "Permissao atualizada no modo local."

    access = get_access_profile(client=resolved_client)
    if not access.get("is_admin"):
        return False, "Apenas admin pode alterar essa permissao."

    payload = {
        "key": CADASTRO_OPEN_SETTING_KEY,
        "value_bool": bool(enabled),
        "updated_by": access.get("user_id"),
    }

    try:
        resolved_client.table(APP_SETTINGS_TABLE).upsert(payload, on_conflict="key").execute()
    except Exception as exc:
        return False, f"Falha ao salvar permissao no Supabase: {exc}"

    _set_cadastro_open_cache(bool(enabled))
    return True, "Permissao de cadastro atualizada com sucesso."


def can_access_cadastro(client: Any | None = None) -> bool:
    access = get_access_profile(client=client)
    if access.get("is_admin"):
        return True

    open_flag = get_cadastro_open_setting(client=client)
    return bool(access.get("authenticated")) and open_flag


def require_cadastro_access(feature_name: str, client: Any | None = None) -> bool:
    if can_access_cadastro(client=client):
        return True

    st.error(f"Acesso restrito: sem permissao para usar '{feature_name}'.")
    st.info("Regra padrao: apenas admin. Para liberar a todos autenticados, defina CADASTRO_OPEN_TO_AUTHENTICATED=true.")
    return False


def require_admin_access(feature_name: str, client: Any | None = None) -> bool:
    access = get_access_profile(client=client)
    if access.get("is_admin"):
        return True

    st.error(f"Acesso restrito: apenas administrador pode usar '{feature_name}'.")
    st.info("Regra de acesso: usuarios_app.id = auth.uid(), ativo = true e role = 'admin'.")
    return False
