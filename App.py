from pathlib import Path

import streamlit as st
from supabase import create_client

from auth.login import render_login
from core.navigation import AppContext, Route, Router, render_navigation_sidebar
from core.session_manager import SessionManager
from page import cadastro, consulta, diagnostico, edit, motor_detail

st.set_page_config(page_title="Moto-Renow", page_icon="⚙️", layout="wide")


@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def bootstrap_styles() -> None:
    css_path = Path(__file__).resolve().parent / "assets" / "style.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def build_router() -> Router:
    router = Router()
    router.register(Route.CADASTRO, cadastro.render)
    router.register(Route.CONSULTA, consulta.render)
    router.register(Route.DETALHE, motor_detail.render)
    router.register(Route.EDIT, edit.render)
    router.register(Route.DIAGNOSTICO, diagnostico.render)
    return router


def main() -> None:
    bootstrap_styles()

    session = SessionManager()
    session.bootstrap()

    if not render_login(session):
        st.stop()

    supabase = init_connection()
    router = build_router()

    render_navigation_sidebar(session)

    ctx = AppContext(supabase=supabase, session=session, router=router)
    router.dispatch(ctx, session.get_route())


if __name__ == "__main__":
    main()
