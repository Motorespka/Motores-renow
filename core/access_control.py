from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Set

import streamlit as st

ADMIN_ROLES = {"admin", "owner", "superadmin", "root"}
PAID_PLANS = {"paid", "pro", "premium", "enterprise", "business"}
DEFAULT_PLAN = "free"
ACCESS_TIER_LABELS = {
    "anon": "Visitante",
    "teaser": "Free (teaser)",
    "cadastro": "Free + cadastro liberado",
    "paid": "Pago",
    "admin": "Admin",
}
CADASTRO_ACCESS_TABLE = "cadastro_access"
CADASTRO_USER_ACCESS_CACHE_PREFIX = "_cadastro_user_access_"
CADASTRO_ACCESS_LIST_CACHE_KEY = "_cadastro_access_list_cache"
CADASTRO_ACCESS_CACHE_TTL_SECONDS = 15


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


def _user_access_cache_key(user_id: str) -> str:
    return f"{CADASTRO_USER_ACCESS_CACHE_PREFIX}{user_id}"


def _set_cadastro_user_access_cache(user_id: str, value: bool) -> None:
    if not user_id:
        return
    st.session_state[_user_access_cache_key(user_id)] = {
        "value": bool(value),
        "ts": float(time.time()),
    }


def _get_cached_cadastro_user_access(user_id: str) -> bool | None:
    if not user_id:
        return None
    cached = st.session_state.get(_user_access_cache_key(user_id))
    if not isinstance(cached, dict):
        return None
    ts = float(cached.get("ts") or 0.0)
    if (time.time() - ts) > CADASTRO_ACCESS_CACHE_TTL_SECONDS:
        return None
    return bool(cached.get("value"))


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
                .select("id,email,username,nome,role,plan,ativo")
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
                .select("id,email,username,nome,role,plan,ativo")
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
                .select("id,email,username,nome,role,plan,ativo")
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
    profile_cache = _current_profile()
    is_local_runtime = bool(getattr(resolved_client, "is_local_runtime", False)) if resolved_client is not None else False
    auth_flag = bool(st.session_state.get("auth_is_authenticated"))
    authenticated = bool(user_id) and (auth_flag or bool(email))
    cache_key = f"{user_id}|{email}|{int(authenticated)}"

    if not force_refresh and st.session_state.get("_access_cache_key") == cache_key:
        cached = st.session_state.get("_access_cache_value")
        if isinstance(cached, dict):
            return cached

    db_profile = _fetch_usuarios_app_profile(user_id, email, resolved_client)
    role = _to_text((db_profile or {}).get("role")).lower()
    plan = _to_text((db_profile or {}).get("plan")).lower() or DEFAULT_PLAN
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

    # Compatibilidade com a tabela `admin` consultada no login.
    if authenticated and not is_admin and _to_bool(profile_cache.get("_admin_match")):
        is_admin = True
        source = "admin_table"
        if not role:
            role = _to_text(profile_cache.get("role")).lower() or "admin"
        if plan == DEFAULT_PLAN:
            plan = _to_text(profile_cache.get("plan")).lower() or DEFAULT_PLAN
        if not db_profile:
            ativo = True

    # No runtime local (localhost), permite bootstrap de admin via perfil local.
    if authenticated and not is_admin and is_local_runtime:
        profile_role = _to_text(profile_cache.get("role")).lower()
        profile_plan = _to_text(profile_cache.get("plan")).lower()
        profile_admin = _to_bool(profile_cache.get("is_admin"))
        local_mode = _to_bool(profile_cache.get("local_mode"))
        if profile_admin or profile_role in ADMIN_ROLES or local_mode:
            is_admin = True
            source = "local_profile"
            if not role:
                role = profile_role or "admin"
        if plan == DEFAULT_PLAN and profile_plan:
            plan = profile_plan
        if not db_profile:
            ativo = True

    if is_admin and not role:
        role = "admin"

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


def has_paid_plan(plan_value: Any) -> bool:
    plan = _to_text(plan_value).lower()
    return plan in PAID_PLANS


def resolve_access_tier(client: Any | None = None) -> str:
    access = get_access_profile(client=client)
    if not access.get("authenticated"):
        return "anon"
    if access.get("is_admin"):
        return "admin"
    if has_paid_plan(access.get("plan")):
        return "paid"

    user_id = _to_text(access.get("user_id"))
    if has_cadastro_user_access(user_id=user_id, client=client):
        return "cadastro"
    return "teaser"


def describe_access_tier(tier: str) -> str:
    key = _to_text(tier).lower()
    return ACCESS_TIER_LABELS.get(key, "Acesso personalizado")


def can_access_paid_features(client: Any | None = None) -> bool:
    access = get_access_profile(client=client)
    if not access.get("authenticated"):
        return False
    if access.get("is_admin"):
        return True
    return has_paid_plan(access.get("plan"))


def require_paid_access(feature_name: str, client: Any | None = None) -> bool:
    if can_access_paid_features(client=client):
        return True

    st.error(f"Recurso pago: '{feature_name}' disponivel somente para plano ativo.")
    st.info("Seu acesso atual e teaser. Fale com o admin para ativar plano pago.")
    return False


def _fetch_cadastro_user_access_from_db(user_id: str, client: Any | None = None) -> bool:
    resolved_client = _resolve_supabase_client(client)
    if resolved_client is None or getattr(resolved_client, "is_local_runtime", False):
        return False
    if not user_id:
        return False

    try:
        res = (
            resolved_client
            .table(CADASTRO_ACCESS_TABLE)
            .select("user_id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = getattr(res, "data", None) or []
        return bool(rows)
    except Exception:
        return False


def has_cadastro_user_access(user_id: str, client: Any | None = None, force_refresh: bool = False) -> bool:
    if not user_id:
        return False

    if not force_refresh:
        cached = _get_cached_cadastro_user_access(user_id)
        if cached is not None:
            return cached

    allowed = _fetch_cadastro_user_access_from_db(user_id=user_id, client=client)
    _set_cadastro_user_access_cache(user_id, allowed)
    return allowed


def _set_cadastro_access_list_cache(rows: List[Dict[str, Any]]) -> None:
    st.session_state[CADASTRO_ACCESS_LIST_CACHE_KEY] = {
        "rows": rows,
        "ts": float(time.time()),
    }


def _get_cached_cadastro_access_list() -> List[Dict[str, Any]] | None:
    cached = st.session_state.get(CADASTRO_ACCESS_LIST_CACHE_KEY)
    if not isinstance(cached, dict):
        return None
    ts = float(cached.get("ts") or 0.0)
    if (time.time() - ts) > CADASTRO_ACCESS_CACHE_TTL_SECONDS:
        return None
    rows = cached.get("rows")
    if isinstance(rows, list):
        return rows
    return None


def list_cadastro_allowed_users(client: Any | None = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
    resolved_client = _resolve_supabase_client(client)
    if resolved_client is None:
        return []

    access = get_access_profile(client=resolved_client)
    if not access.get("is_admin"):
        return []

    if getattr(resolved_client, "is_local_runtime", False):
        return []

    if not force_refresh:
        cached = _get_cached_cadastro_access_list()
        if cached is not None:
            return cached

    try:
        res = (
            resolved_client
            .table(CADASTRO_ACCESS_TABLE)
            .select("user_id,created_at")
            .order("created_at", desc=True)
            .limit(200)
            .execute()
        )
        grant_rows = getattr(res, "data", None) or []
    except Exception:
        return []

    user_ids = [_to_text(r.get("user_id")) for r in grant_rows if _to_text(r.get("user_id"))]
    user_ids = list(dict.fromkeys(user_ids))
    if not user_ids:
        _set_cadastro_access_list_cache([])
        return []

    profiles_map: Dict[str, Dict[str, Any]] = {}

    try:
        res_profiles = (
            resolved_client
            .table("usuarios_app")
            .select("id,username,nome,email,role,ativo")
            .in_("id", user_ids)
            .execute()
        )
        profile_rows = getattr(res_profiles, "data", None) or []
        for row in profile_rows:
            if isinstance(row, dict):
                uid = _to_text(row.get("id"))
                if uid:
                    profiles_map[uid] = row
    except Exception:
        for uid in user_ids:
            try:
                res_one = (
                    resolved_client
                    .table("usuarios_app")
                    .select("id,username,nome,email,role,ativo")
                    .eq("id", uid)
                    .limit(1)
                    .execute()
                )
                rows = getattr(res_one, "data", None) or []
                if rows and isinstance(rows[0], dict):
                    profiles_map[uid] = rows[0]
            except Exception:
                continue

    output: List[Dict[str, Any]] = []
    for item in grant_rows:
        if not isinstance(item, dict):
            continue
        uid = _to_text(item.get("user_id"))
        if not uid:
            continue
        profile = profiles_map.get(uid, {})
        username = _to_text(profile.get("username"))
        nome = _to_text(profile.get("nome"))
        email = _to_text(profile.get("email")).lower()
        display = username or nome or (email.split("@", 1)[0] if email and "@" in email else uid)
        label = f"{display} ({email or uid})"
        output.append(
            {
                "user_id": uid,
                "display": display,
                "label": label,
                "username": username,
                "nome": nome,
                "email": email,
                "created_at": _to_text(item.get("created_at")),
            }
        )

    _set_cadastro_access_list_cache(output)
    return output


def search_usuarios_for_cadastro_access(
    query_text: str,
    client: Any | None = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    resolved_client = _resolve_supabase_client(client)
    if resolved_client is None or getattr(resolved_client, "is_local_runtime", False):
        return []

    access = get_access_profile(client=resolved_client)
    if not access.get("is_admin"):
        return []

    query = _to_text(query_text).lower()
    if len(query) < 2:
        return []

    merged: Dict[str, Dict[str, Any]] = {}
    for field in ["username", "nome", "email"]:
        try:
            res = (
                resolved_client
                .table("usuarios_app")
                .select("id,username,nome,email,role,plan,ativo")
                .ilike(field, f"%{query}%")
                .limit(limit)
                .execute()
            )
            rows = getattr(res, "data", None) or []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                uid = _to_text(row.get("id"))
                if uid:
                    merged[uid] = row
        except Exception:
            continue

    output: List[Dict[str, Any]] = []
    for uid, row in merged.items():
        username = _to_text(row.get("username"))
        nome = _to_text(row.get("nome"))
        email = _to_text(row.get("email")).lower()
        display = username or nome or (email.split("@", 1)[0] if email and "@" in email else uid)
        label = f"{display} ({email or uid})"
        output.append(
            {
                "user_id": uid,
                "display": display,
                "label": label,
                "username": username,
                "nome": nome,
                "email": email,
                "role": _to_text(row.get("role")).lower(),
                "plan": _to_text(row.get("plan")).lower() or DEFAULT_PLAN,
                "ativo": _to_bool(row.get("ativo")),
            }
        )

    output.sort(key=lambda item: (_to_text(item.get("display")).lower(), _to_text(item.get("email")).lower()))
    return output[:limit]


def get_usuario_for_admin(user_id: str, client: Any | None = None) -> Dict[str, Any] | None:
    resolved_client = _resolve_supabase_client(client)
    if resolved_client is None:
        return None

    access = get_access_profile(client=resolved_client)
    if not access.get("is_admin"):
        return None

    uid = _to_text(user_id)
    if not uid:
        return None

    if getattr(resolved_client, "is_local_runtime", False):
        me = _current_profile()
        if _to_text(me.get("id")) == uid or _to_text(st.session_state.get("auth_user_id")) == uid:
            return {
                "id": uid,
                "username": _to_text(me.get("username")),
                "nome": _to_text(me.get("nome")),
                "email": _normalized_email(me.get("email")),
                "role": _to_text(me.get("role")).lower() or "admin",
                "plan": _to_text(me.get("plan")).lower() or DEFAULT_PLAN,
                "ativo": True,
            }
        return None

    try:
        res = (
            resolved_client
            .table("usuarios_app")
            .select("id,username,nome,email,role,plan,ativo,created_at,updated_at")
            .eq("id", uid)
            .limit(1)
            .execute()
        )
        rows = getattr(res, "data", None) or []
        if not rows or not isinstance(rows[0], dict):
            return None
        row = rows[0]
        return {
            "id": _to_text(row.get("id")),
            "username": _to_text(row.get("username")),
            "nome": _to_text(row.get("nome")),
            "email": _normalized_email(row.get("email")),
            "role": _to_text(row.get("role")).lower(),
            "plan": _to_text(row.get("plan")).lower() or DEFAULT_PLAN,
            "ativo": _to_bool(row.get("ativo")),
            "created_at": _to_text(row.get("created_at")),
            "updated_at": _to_text(row.get("updated_at")),
        }
    except Exception:
        return None


def update_usuario_for_admin(
    user_id: str,
    *,
    username: str,
    nome: str,
    role: str,
    plan: str,
    ativo: bool,
    client: Any | None = None,
) -> tuple[bool, str]:
    resolved_client = _resolve_supabase_client(client)
    if resolved_client is None:
        return False, "Cliente Supabase indisponivel."

    access = get_access_profile(client=resolved_client)
    if not access.get("is_admin"):
        return False, "Apenas admin pode alterar usuarios."

    uid = _to_text(user_id)
    if not uid:
        return False, "Usuario invalido."

    username_norm = _to_text(username).lower()
    nome_norm = _to_text(nome)
    role_norm = _to_text(role).lower() or "user"
    plan_norm = _to_text(plan).lower() or DEFAULT_PLAN

    if role_norm not in {"user", "admin"}:
        return False, "Role invalida. Use 'user' ou 'admin'."
    if plan_norm not in (PAID_PLANS | {DEFAULT_PLAN}):
        return False, f"Plano invalido. Use: {DEFAULT_PLAN}, {', '.join(sorted(PAID_PLANS))}."
    if not username_norm:
        return False, "Username nao pode ficar vazio."

    payload = {
        "username": username_norm,
        "nome": nome_norm or None,
        "role": role_norm,
        "plan": plan_norm,
        "ativo": bool(ativo),
    }

    if getattr(resolved_client, "is_local_runtime", False):
        if uid == _to_text(st.session_state.get("auth_user_id")):
            profile = dict(_current_profile())
            profile.update(
                {
                    "username": username_norm,
                    "nome": nome_norm,
                    "role": role_norm,
                    "plan": plan_norm,
                    "ativo": bool(ativo),
                }
            )
            st.session_state["auth_user_profile"] = profile
            st.session_state.pop("_access_cache_key", None)
            st.session_state.pop("_access_cache_value", None)
            return True, "Atualizado em modo local."
        return False, "Atualizacao de outros usuarios indisponivel em modo local."

    try:
        resolved_client.table("usuarios_app").update(payload).eq("id", uid).execute()
    except Exception as exc:
        msg = _to_text(exc).lower()
        if any(token in msg for token in ["row level", "rls", "permission", "not authorized", "forbidden"]):
            return False, "Sem permissao de escrita (RLS). Ajuste as policies de admin na tabela usuarios_app."
        return False, f"Falha ao atualizar usuario: {exc}"

    st.session_state.pop("_access_cache_key", None)
    st.session_state.pop("_access_cache_value", None)
    st.session_state.pop("_admin_cache_key", None)
    st.session_state.pop("_admin_cache_value", None)
    _set_cadastro_user_access_cache(uid, has_cadastro_user_access(uid, client=resolved_client, force_refresh=True))
    return True, "Usuario atualizado com sucesso."


def grant_cadastro_access_for_user(user_id: str, client: Any | None = None) -> tuple[bool, str]:
    resolved_client = _resolve_supabase_client(client)
    if resolved_client is None:
        return False, "Cliente Supabase indisponivel."

    access = get_access_profile(client=resolved_client)
    if not access.get("is_admin"):
        return False, "Apenas admin pode adicionar permissao."

    uid = _to_text(user_id)
    if not uid:
        return False, "Selecione um usuario valido."

    if getattr(resolved_client, "is_local_runtime", False):
        _set_cadastro_user_access_cache(uid, True)
        st.session_state.pop(CADASTRO_ACCESS_LIST_CACHE_KEY, None)
        return True, "Permissao aplicada em modo local."

    payload = {"user_id": uid, "added_by": access.get("user_id")}
    try:
        resolved_client.table(CADASTRO_ACCESS_TABLE).upsert(payload, on_conflict="user_id").execute()
    except Exception as exc:
        return False, f"Falha ao conceder permissao: {exc}"

    _set_cadastro_user_access_cache(uid, True)
    st.session_state.pop(CADASTRO_ACCESS_LIST_CACHE_KEY, None)
    return True, "Permissao de cadastro concedida."


def revoke_cadastro_access_for_user(user_id: str, client: Any | None = None) -> tuple[bool, str]:
    resolved_client = _resolve_supabase_client(client)
    if resolved_client is None:
        return False, "Cliente Supabase indisponivel."

    access = get_access_profile(client=resolved_client)
    if not access.get("is_admin"):
        return False, "Apenas admin pode remover permissao."

    uid = _to_text(user_id)
    if not uid:
        return False, "Usuario invalido."

    if getattr(resolved_client, "is_local_runtime", False):
        _set_cadastro_user_access_cache(uid, False)
        st.session_state.pop(CADASTRO_ACCESS_LIST_CACHE_KEY, None)
        return True, "Permissao removida em modo local."

    try:
        resolved_client.table(CADASTRO_ACCESS_TABLE).delete().eq("user_id", uid).execute()
    except Exception as exc:
        return False, f"Falha ao remover permissao: {exc}"

    _set_cadastro_user_access_cache(uid, False)
    st.session_state.pop(CADASTRO_ACCESS_LIST_CACHE_KEY, None)
    return True, "Permissao de cadastro removida."


def can_access_cadastro(client: Any | None = None) -> bool:
    access = get_access_profile(client=client)
    if access.get("is_admin"):
        return True

    if not access.get("authenticated"):
        return False

    if has_paid_plan(access.get("plan")):
        return True

    user_id = _to_text(access.get("user_id"))
    return has_cadastro_user_access(user_id=user_id, client=client)


def require_cadastro_access(feature_name: str, client: Any | None = None) -> bool:
    if can_access_cadastro(client=client):
        return True

    st.error(f"Acesso restrito: sem permissao para usar '{feature_name}'.")
    st.info("Acesso permitido para admin, plano pago ou usuario liberado manualmente pelo admin.")
    return False


def require_admin_access(feature_name: str, client: Any | None = None) -> bool:
    access = get_access_profile(client=client)
    if access.get("is_admin"):
        return True

    st.error(f"Acesso restrito: apenas administrador pode usar '{feature_name}'.")
    st.info("Regra de acesso: usuarios_app.id = auth.uid(), ativo = true e role = 'admin'.")
    return False
