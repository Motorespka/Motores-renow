import streamlit as st
from auth.session import limpar_sessao


def botao_logout():
    if st.sidebar.button("🚪 Sair"):
        limpar_sessao()
        st.rerun()
