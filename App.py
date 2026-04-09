from pathlib import Path

import streamlit as st
try:
    from supabase import create_client
except Exception:
    create_client = None

from auth.login import render_login, sync_authenticated_profile
from core.access_control import is_admin_user
from core.navigation import AppContext, Route, Router, render_navigation_sidebar
from core.session_manager import SessionManager
from page import cadastro, consulta, diagnostico, edit, motor_detail
from services.database import bootstrap_database, build_local_runtime_client

st.set_page_config(page_title="Moto-Renow", page_icon="⚙️", layout="wide")


@st.cache_resource
def init_connection(mode: str):
    if mode == "DEV":
        return build_local_runtime_client(mode="DEV")

    if create_client is None:
        raise RuntimeError("SDK do Supabase indisponivel neste ambiente.")
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
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
    client.table("motores").select("id").limit(1).execute()


def resolve_runtime_mode() -> str:
    try:
        env = str(st.secrets.get("ENV", "PROD")).strip().upper()
    except Exception:
        env = "PROD"
    return env or "PROD"


def connect_runtime_client(mode: str):
    if mode == "DEV":
        return init_connection("DEV")

    try:
        runtime = init_connection("PROD")
        validate_database_schema(runtime)
        return runtime
    except Exception:
        # Em falha de Supabase, usa fallback local sem parar o app.
        return build_local_runtime_client(mode="FALLBACK")


def main() -> None:
    session = SessionManager()
    try:
        bootstrap_system(session)
    except Exception as exc:
        st.error(f"Falha na inicializacao do sistema: {exc}")
        return

    runtime_mode = resolve_runtime_mode()
    client = connect_runtime_client(runtime_mode)

    if runtime_mode == "DEV" or getattr(client, "is_local_runtime", False):
        st.warning("⚠️ MODO DEV ATIVO")

    if not render_login(session, client):
        st.stop()

    sync_authenticated_profile(session, client)

    current_route = session.get_route()
    if not is_admin_user() and current_route in {Route.CADASTRO, Route.EDIT}:
        session.set_route(Route.CONSULTA)

    router = build_router()
    render_navigation_sidebar(session)

    ctx = AppContext(supabase=client, session=session, router=router)
    router.dispatch(ctx, session.get_route())


if __name__ == "__main__":
    main()
