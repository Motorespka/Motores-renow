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
from core.access_control import can_access_cadastro, can_access_paid_features, get_access_profile
from core.navigation import AppContext, Route, Router, render_navigation_sidebar
from core.session_manager import SessionManager
from page import admin_panel, cadastro, consulta, diagnostico, edit, motor_detail
from services.database import bootstrap_database, build_local_runtime_client

params= st.query_params

if "token" in params and "user" not in 
st.session_state:
        token = params["token"]
        usuario = validar_token(token)

    if usuario:
        st.session_state["user"] = usuario 
        
st.set_page_config(page_title="Moto-Renow", page_icon="⚙️", layout="wide")
DEBUG_ACCESS = str(os.environ.get("DEBUG_ACCESS", "")).strip().lower() in {"1", "true", "yes", "on"}


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


def _resolve_browser_cache_key() -> str:
    cached = st.session_state.get("_browser_cache_key")
    if isinstance(cached, str) and cached.strip():
        return cached

    cookies = {}
    headers = {}
    try:
        cookies = _to_plain_mapping(getattr(st.context, "cookies", {}))
    except Exception:
        cookies = {}
    try:
        headers = _to_plain_mapping(getattr(st.context, "headers", {}))
    except Exception:
        headers = {}

    fingerprint = {
        "cookies": cookies,
        "user_agent": headers.get("user-agent", ""),
        "accept_language": headers.get("accept-language", ""),
        "host": headers.get("host", ""),
    }
    serialized = json.dumps(fingerprint, sort_keys=True, ensure_ascii=True)
    if serialized and serialized != "{}":
        key = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:24]
    else:
        key = uuid.uuid4().hex[:24]

    
    return key


def init_connection(mode: str, ):
   
    if mode == "DEV":
        return build_local_runtime_client(mode="DEV")

    if create_client is None:
        raise RuntimeError("SDK do Supabase indisponivel neste ambiente.")

    url = _read_secret_or_env("SUPABASE_URL")
    key = _read_secret_or_env("SUPABASE_KEY", "SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL/SUPABASE_KEY (ou SUPABASE_ANON_KEY) nao configurados.")

    return create_client(url, key)


def bootstrap_styles() -> None:
    css_path = Path(__file__).resolve().parent / "assets" / "style.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def build_router() -> Router:
    router = Router()
    router.register(Route.CADASTRO, cadastro.show)
    router.register(Route.CONSULTA, consulta.show)
    router.register(Route.DETALHE, motor_detail.show)
    router.register(Route.EDIT, edit.show)
    router.register(Route.DIAGNOSTICO, diagnostico.show)
    router.register(Route.ADMIN, admin_panel.show)
    return router


def bootstrap_system(session: SessionManager) -> None:
    bootstrap_database()
    session.bootstrap()
    try:
        bootstrap_styles()
    except Exception:
        # Estilo e opcional; nao derruba o runtime.
        pass


def validate_database_schema(client) -> None:
    try:
        client.table("motores").select("id").limit(1).execute()
    except Exception as exc:
        msg = str(exc).lower()
        # Em ambientes com RLS estrita para usuarios autenticados,
        # este teste pode falhar antes do login.
        if any(token in msg for token in ["permission", "row level", "rls", "jwt", "not authenticated"]):
            return
        raise


def resolve_runtime_mode() -> str:
    env_var = str(os.environ.get("ENV", "")).strip().upper()
    if env_var:
        return env_var

    try:
        env = str(st.secrets.get("ENV", "PROD")).strip().upper()
    except Exception:
        env = ""
    if env:
        return env

    has_supabase = bool(_read_secret_or_env("SUPABASE_URL")) and bool(
        _read_secret_or_env("SUPABASE_KEY", "SUPABASE_ANON_KEY")
    )

    if not has_supabase:
        return "DEV"

    env = "PROD"
    return env or "PROD"


def connect_runtime_client(mode: str):
    target_mode = "DEV" if str(mode).upper() == "DEV" else "PROD"
    cache_key = _resolve_browser_cache_key()

    if target_mode == "DEV":
        runtime = init_connection("DEV")
    else:
        runtime = init_connection("PROD")
        validate_database_schema(runtime)

    st.session_state["_runtime_client"] = runtime
    st.session_state["_runtime_client_mode"] = target_mode
    st.session_state["_runtime_client_cache_key"] = cache_key
    return runtime


def _read_route_state(session: SessionManager) -> str:
    route = st.session_state.get("route")
    if isinstance(route, str) and route.strip():
        return route.strip().lower()
    try:
        route = session.get_route().value
    except Exception:
        route = ""
    route = str(route or "").strip().lower()
    st.session_state["route"] = route
    return route


def _set_route_state(session: SessionManager, route_value: str) -> None:
    route_value = str(route_value or "").strip().lower()
    st.session_state["route"] = route_value
    if route_value in {r.value for r in Route}:
        session.set_route(Route(route_value))


def _debug_access_state(access: dict, current_before: str, current_after: str) -> None:
    if not DEBUG_ACCESS:
        return
    supabase_url = _read_secret_or_env("SUPABASE_URL")
    supabase_key = _read_secret_or_env("SUPABASE_KEY", "SUPABASE_ANON_KEY")
    project_ref = ""
    if ".supabase.co" in supabase_url:
        try:
            project_ref = supabase_url.split("://", 1)[-1].split(".supabase.co", 1)[0]
        except Exception:
            project_ref = ""
    expected_project_ref = _read_secret_or_env("SUPABASE_PROJECT_REF", "EXPECTED_SUPABASE_PROJECT_REF")
    project_ref_match = None
    if expected_project_ref:
        project_ref_match = project_ref == expected_project_ref
    masked_key = ""
    if supabase_key:
        if len(supabase_key) > 12:
            masked_key = f"{supabase_key[:6]}...{supabase_key[-4:]}"
        else:
            masked_key = f"{supabase_key[:3]}..."

    st.write("DEBUG auth_user_id:", st.session_state.get("auth_user_id"))
    st.write("DEBUG auth_user_email:", st.session_state.get("auth_user_email"))
    st.write("DEBUG auth_user_profile:", st.session_state.get("auth_user_profile"))
    st.write(
        "DEBUG supabase_env:",
        {
            "url_partial": (supabase_url[:28] + "...") if supabase_url else "",
            "project_ref": project_ref,
            "expected_project_ref": expected_project_ref,
            "project_ref_match": project_ref_match,
            "anon_key_masked": masked_key,
            "client_initialized": st.session_state.get("_supabase_client") is not None,
            "is_local_runtime": bool(getattr(st.session_state.get("_supabase_client"), "is_local_runtime", False)),
        },
    )
    st.write("DEBUG access:", access)
    st.write("DEBUG _perfil_debug:", st.session_state.get("_perfil_debug"))
    st.write("DEBUG _access_profile_debug:", st.session_state.get("_access_profile_debug"))
    st.write("DEBUG current_route_before:", current_before)
    st.write("DEBUG current_route_after:", current_after)


def main() -> None:
    session = SessionManager()
    try:
        bootstrap_system(session)
    except Exception as exc:
        st.error(f"Falha na inicializacao do sistema: {exc}")
        return

    runtime_mode = resolve_runtime_mode()
    try:
        client = connect_runtime_client(runtime_mode)
    except Exception as exc:
        st.error(f"Falha ao conectar no banco de producao: {exc}")
        st.stop()
    st.session_state["_supabase_client"] = client

    if runtime_mode == "DEV" or getattr(client, "is_local_runtime", False):
        st.warning("⚠️ MODO DEV ATIVO")

    if not render_login(session, client):
        st.session_state["route"] = "login"
        st.stop()

    sync_authenticated_profile(session, client)
    access = get_access_profile(client=client)
    paid_allowed = can_access_paid_features(client=client)
    cadastro_allowed = can_access_cadastro(client=client)
    current_route_before = _read_route_state(session)
    current_route = current_route_before

    if not access.get("authenticated"):
        st.session_state["route"] = "login"
    else:
        if cadastro_allowed:
            if current_route in {"", "login", "consulta"}:
                _set_route_state(session, "cadastro")
        else:
            if current_route in {"", "login", "cadastro", "edit", "diagnostico", "detalhe", "admin"}:
                _set_route_state(session, "consulta")

    current_route_after = _read_route_state(session)
    _debug_access_state(access, current_route_before, current_route_after)

    if not access.get("authenticated"):
        st.stop()

    route = st.session_state.get("route", "login")
    if access.get("authenticated") and cadastro_allowed and route == "consulta":
        _set_route_state(session, "cadastro")
        st.rerun()

    if access.get("authenticated") and (not cadastro_allowed) and route == "cadastro":
        _set_route_state(session, "consulta")
        st.rerun()

    if access.get("authenticated") and (not access.get("is_admin")) and route == "edit":
        _set_route_state(session, "consulta")
        st.rerun()

    if access.get("authenticated") and (not access.get("is_admin")) and route == "admin":
        _set_route_state(session, "consulta")
        st.rerun()

    if access.get("authenticated") and (not paid_allowed) and route in ("diagnostico", "detalhe"):
        _set_route_state(session, "consulta")
        st.rerun()

    router = build_router()
    render_navigation_sidebar(session, client)

    ctx = AppContext(supabase=client, session=session, router=router)
    router.dispatch(ctx, session.get_route())


if __name__ == "__main__":
    main()
