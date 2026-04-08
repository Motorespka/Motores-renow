import streamlit as st

from auth.session import limpar_sessao, sessao_valida


def check_login():
    """
    Módulo legado: mantém apenas verificação de sessão + logout.
    A autenticação principal está em auth/login.py via Supabase Auth.
    """
    if sessao_valida():
        if st.sidebar.button("🚪 Sair"):
            limpar_sessao()
            st.rerun()
        return True

    st.info("Faça login pela tela principal.")
    st.stop()
