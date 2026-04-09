from pathlib import Path
import os

import streamlit as st
try:
    from supabase import create_client
except Exception:
    create_client = None

from auth.login import render_login, sync_authenticated_profile
from core.navigation import AppContext, Route, Router, render_navigation_sidebar
from core.session_manager import SessionManager
from page import cadastro, consulta, diagnostico, edit, motor_detail
from services.database import bootstrap_database, build_local_runtime_client

st.set_page_config(page_title="Moto-Renow", page_icon="⚙️", layout="wide")


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


@st.cache_resource
def init_connection(mode: str):
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
    if mode == "DEV":
        return init_connection("DEV")

    runtime = init_connection("PROD")
    validate_database_schema(runtime)
    return runtime


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
        st.stop()

    sync_authenticated_profile(session, client)

    # Nao forcamos redirecionamento de rota aqui:
    # a propria pagina protegida (cadastro/edit) bloqueia o acesso para nao-admin.
    # Isso evita "pulo" visual de /?route=cadastro para /?route=consulta
    # quando a verificacao de perfil oscila por sincronizacao.
    session.get_route()

    router = build_router()
    render_navigation_sidebar(session, client)

    ctx = AppContext(supabase=client, session=session, router=router)
    router.dispatch(ctx, session.get_route())


if __name__ == "__main__":
    main()
