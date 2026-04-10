from pathlib import Path
import hashlib
import json
import os
import uuid

import streamlit as st

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


# =========================================================
# ⭐ CORREÇÃO REAL DA SESSÃO (NÃO QUEBRA NADA)
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
        key = hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()[:24]
    else:
        key = uuid.uuid4().hex[:24]

    # ⭐ salva definitivamente
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
# MAIN
# =========================================================

def main():

    session = SessionManager()

    try:
        bootstrap_system(session)
    except Exception as exc:
        st.error(f"Falha na inicialização: {exc}")
        return

    runtime_mode = resolve_runtime_mode()

    try:
        client = connect_runtime_client(runtime_mode)
    except Exception as exc:
        st.error(f"Falha ao conectar banco: {exc}")
        st.stop()

    st.session_state["_supabase_client"] = client

    # LOGIN
    if not render_login(session, client):
        st.stop()

    sync_authenticated_profile(session, client)

    access = get_access_profile(client=client)
    paid_allowed = can_access_paid_features(client=client)
    cadastro_allowed = can_access_cadastro(client=client)

    if not access.get("authenticated"):
        st.stop()

    router = build_router()

    render_navigation_sidebar(session, client)

    ctx = AppContext(
        supabase=client,
        session=session,
        router=router,
    )

    router.dispatch(ctx, session.get_route())


if __name__ == "__main__":
    main()
