import streamlit as st
from auth.session import criar_sessao, sessao_valida


def check_login():
    if sessao_valida():
        return True

    st.title("🔐 Moto-Renow • Acesso Técnico")
    senha = st.text_input("Chave técnica", type="password")

    if st.button("Entrar"):
        if senha == st.secrets["APP_PASSWORD"]:
            criar_sessao()
            st.rerun()
        else:
            st.error("Senha incorreta")

    st.stop()
