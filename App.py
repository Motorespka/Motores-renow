from pathlib import Path
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import streamlit as st

try:
    import extra_streamlit_components as stx
except Exception:
    stx = None

try:
    from supabase import create_client
except Exception:
    create_client = None

from auth.login import render_login, sync_authenticated_profile
from core.access_control import (
    can_access_cadastro,
    can_access_paid_features,
    get_access_profile,
)
from core.navigation import AppContext, Route, Router, render_navigation_sidebar
from core.session_manager import SessionManager
from page import admin_panel, cadastro, consulta, diagnostico, edit, motor_detail
from services.database import bootstrap_database, build_local_runtime_client


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="Moto-Renow", page_icon="⚙️", layout="wide")

DEBUG_ACCESS = str(os.environ.get("DEBUG_ACCESS", "")).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

AUTH_COOKIE_NAME = "moto_renow_auth_v1"
AUTH_COOKIE_DAYS = 30


# =========================================================
# UTILS
# =========================================================

def _read_secret_or_env(*names: str) -> str:
    for name in names:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass

        value = os.environ.get(name)
        if value:
            return str(value).strip()

    return ""


def _to_plain_mapping(value) -> dict:
    try:
        if value is None:
            return {}
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        return {str(k): str(v) for k, v in dict(value).items()}
    except Exception:
        return {}


def _json_dumps_safe(data: dict) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return "{}"


def _json_loads_safe(raw: str) -> dict:
    try:
        if not raw:
            return {}
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


# =========================================================
# COOKIE AUTH
# =========================================================

def _get_cookie_manager():
    if stx is None:
        return None

    if "_cookie_manager" not in st.session_state:
        st.session_state["_cookie_manager"] = stx.CookieManager()

    return st.session_state["_cookie_manager"]


def _cookie_available() -> bool:
    return _get_cookie_manager() is not None


def _read_auth_cookie() -> dict:
    manager = _get_cookie_manager()
    if manager is None:
        return {}

    try:
        raw = manager.get(AUTH_COOKIE_NAME)
        return _json_loads_safe(raw)
    except Exception:
        return {}


def _write_auth_cookie(data: dict) -> bool:
    manager = _get_cookie_manager()
    if manager is None:
        return False

    try:
        expires_at = datetime.now(timezone.utc) + timedelta(days=AUTH_COOKIE_DAYS)
        manager.set(
            AUTH_COOKIE_NAME,
            _json_dumps_safe(data),
            expires_at=expires_at,
            key=f"set_cookie_{AUTH_COOKIE_NAME}",
        )
        return True
    except Exception:
        return False


def _clear_auth_cookie():
    manager = _get_cookie_manager()
    if manager is None:
        return

    try:
        manager.delete(AUTH_COOKIE_NAME, key=f"delete_cookie_{AUTH_COOKIE_NAME}")
    except Exception:
        pass


def persist_auth_state(client) -> None:
    try:
        payload = {
            "auth_user_id": st.session_state.get("auth_user_id", ""),
            "auth_email": st.session_state.get("auth_email", ""),
            "authenticated": bool(st.session_state.get("authenticated", False)),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_auth_cookie(payload)
    except Exception:
        pass


def clear_auth_state():
    keys = [
        "auth_user_id",
        "auth_email",
        "authenticated",
        "_access_profile",
        "_paid_allowed",
        "_cadastro_allowed",
    ]
    for key in keys:
        st.session_state.pop(key, None)

    _clear_auth_cookie()


def try_restore_auth_session(session, client) -> bool:
    try:
        if st.session_state.get("auth_user_id"):
            st.session_state["authenticated"] = True
            return True

        cookie_data = _read_auth_cookie()
        if not cookie_data:
            return False

        auth_user_id = str(cookie_data.get("auth_user_id", "")).strip()
        auth_email = str(cookie_data.get("auth_email", "")).strip()
        authenticated = bool(cookie_data.get("authenticated", False))

        if not auth_user_id or not authenticated:
            return False

        st.session_state["auth_user_id"] = auth_user_id
        if auth_email:
            st.session_state["auth_email"] = auth_email
        st.session_state["authenticated"] = True

        try:
            sync_authenticated_profile(session, client)
        except Exception:
            pass

        access = get_access_profile(client=client)
        if not access.get("authenticated"):
            clear_auth_state()
            return False

        st.session_state["_access_profile"] = access
        st.session_state["_paid_allowed"] = can_access_paid_features(client=client)
        st.session_state["_cadastro_allowed"] = can_access_cadastro(client=client)

        return True

    except Exception:
        clear_auth_state()
        return False


# =========================================================
# SESSION CACHE KEY
# =========================================================

def _resolve_browser_cache_key() -> str:
    cached = st.session_state.get("_browser_cache_key")
    if isinstance(cached, str) and cached.strip():
        return cached

    cookies = {}
    headers = {}

    try:
        cookies = _to_plain_mapping(getattr(st.context, "cookies", {}))
    except Exception:
        pass

    try:
        headers = _to_plain_mapping(getattr(st.context, "headers", {}))
    except Exception:
        pass

    fingerprint = {
        "cookies": cookies,
        "user_agent": headers.get("user-agent", ""),
        "accept_language": headers.get("accept-language", ""),
        "host": headers.get("host", ""),
    }

    serialized = json.dumps(
        fingerprint,
        sort_keys=True,
        ensure_ascii=True,
    )

    if serialized and serialized != "{}":
        key = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:24]
    else:
        key = uuid.uuid4().hex[:24]

    st.session_state["_browser_cache_key"] = key
    return key


# =========================================================
# DATABASE
# =========================================================

def init_connection(mode: str):
    if mode == "DEV":
        return build_local_runtime_client(mode="DEV")

    if create_client is None:
        raise RuntimeError("SDK do Supabase indisponível.")

    url = _read_secret_or_env("SUPABASE_URL")
    key = _read_secret_or_env("SUPABASE_KEY", "SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError("SUPABASE não configurado.")

    return create_client(url, key)


def bootstrap_styles():
    css_path = Path(__file__).resolve().parent / "assets" / "style.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def bootstrap_system(session: SessionManager):
    bootstrap_database()
    session.bootstrap()
    bootstrap_styles()


def resolve_runtime_mode() -> str:
    env = os.environ.get("ENV", "").upper()
    if env:
        return env

    try:
        return str(st.secrets.get("ENV", "PROD")).upper()
    except Exception:
        return "PROD"


def connect_runtime_client(mode: str):
    cache_key = _resolve_browser_cache_key()

    runtime = init_connection(mode)

    st.session_state["_runtime_client"] = runtime
    st.session_state["_runtime_client_mode"] = mode
    st.session_state["_runtime_client_cache_key"] = cache_key

    return runtime


# =========================================================
# ROUTER
# =========================================================

def build_router() -> Router:
    router = Router()

    router.register(Route.CADASTRO, cadastro.show)
    router.register(Route.CONSULTA, consulta.show)
    router.register(Route.DETALHE, motor_detail.show)
    router.register(Route.EDIT, edit.show)
    router.register(Route.DIAGNOSTICO, diagnostico.show)
    router.register(Route.ADMIN, admin_panel.show)

    return router


# =========================================================
# HELPERS
# =========================================================

def ensure_initial_route(client):
    if "route" in st.session_state and st.session_state["route"]:
        return

    cadastro_allowed = can_access_cadastro(client=client)

    if cadastro_allowed:
        try:
            st.session_state["route"] = Route.CADASTRO
        except Exception:
            st.session_state["route"] = "cadastro"
    else:
        try:
            st.session_state["route"] = Route.CONSULTA
        except Exception:
            st.session_state["route"] = "consulta"


def finalize_authenticated_state(session, client):
    sync_authenticated_profile(session, client)

    access = get_access_profile(client=client)
    paid_allowed = can_access_paid_features(client=client)
    cadastro_allowed = can_access_cadastro(client=client)

    st.session_state["_access_profile"] = access
    st.session_state["_paid_allowed"] = paid_allowed
    st.session_state["_cadastro_allowed"] = cadastro_allowed

    if not st.session_state.get("auth_email"):
        try:
            email = access.get("email")
            if email:
                st.session_state["auth_email"] = email
        except Exception:
            pass

    if access.get("authenticated"):
        st.session_state["authenticated"] = True
        persist_auth_state(client)
        ensure_initial_route(client)


# =========================================================
# MAIN
# =========================================================

def main():
    session = SessionManager()

    try:
        bootstrap_system(session)
    except Exception as exc:
        st.error(f"Falha na inicialização: {exc}")
        return

    if stx is None:
        st.warning(
            "Persistência de login desativada: falta instalar 'extra-streamlit-components'. "
            "Rode: pip install extra-streamlit-components"
        )

    runtime_mode = resolve_runtime_mode()

    try:
        client = connect_runtime_client(runtime_mode)
    except Exception as exc:
        st.error(f"Falha ao conectar banco: {exc}")
        st.stop()

    st.session_state["_supabase_client"] = client

    restored = try_restore_auth_session(session, client)

    if not restored:
        logged = render_login(session, client)

        if not logged:
            st.stop()

        finalize_authenticated_state(session, client)
        st.rerun()

    finalize_authenticated_state(session, client)

    access = st.session_state.get("_access_profile") or get_access_profile(client=client)
    if not access.get("authenticated"):
        clear_auth_state()
        st.stop()

    router = build_router()

    render_navigation_sidebar(session, client)

    with st.sidebar:
        if st.button("Sair", use_container_width=True):
            clear_auth_state()
            st.session_state["route"] = "consulta"
            st.rerun()

    ctx = AppContext(
        supabase=client,
        session=session,
        router=router,
    )

    router.dispatch(ctx, session.get_route())


if __name__ == "__main__":
    main()
