import streamlit as st
from auth.session import criar_sessao, sessao_valida


def check_login():

    # se sessão válida → entra direto
    if sessao_valida():
        return

    st.title("🔐 Moto-Renow • Acesso Técnico")

    senha = st.text_input(
        "Chave técnica",
        type="password"
    )

    if st.button("Entrar"):

        if senha == st.secrets["APP_PASSWORD"]:
            criar_sessao()
            st.success("Acesso liberado")
            st.rerun()
        else:
            st.error("Senha incorreta")

    st.stop()
