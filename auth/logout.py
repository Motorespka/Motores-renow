import streamlit as st


def check_login(session=None):
    """
    Compatibilidade legada: validacao agora usa a sessao principal (Supabase Auth).
    Este modulo nao decide mais rota nem permissao.
    """
    if session is not None and bool(getattr(session, "is_authenticated", False)):
        return True

    if bool(st.session_state.get("auth_is_authenticated", False)):
        return True

    st.info("Faça login pela tela principal.")
    st.stop()
