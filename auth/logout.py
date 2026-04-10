import streamlit as st
from auth.login import logout_and_clear


def perform_logout(session, client):
    logout_and_clear(session, client)
    st.success("Sessão encerrada com sucesso.")
    st.rerun()
