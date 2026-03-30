import streamlit as st

def check_login():

    if "logado" not in st.session_state:
        st.session_state.logado = False

    # já logado
    if st.session_state.logado:
        return

    st.title("🔐 Moto-Renow - Acesso Técnico")

    senha = st.text_input(
        "Digite a chave técnica",
        type="password"
    )

    if st.button("Entrar"):

        if "APP_PASSWORD" not in st.secrets:
            st.error("APP_PASSWORD não encontrada no Secrets")
            st.stop()

        if senha == st.secrets["APP_PASSWORD"]:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta")

    st.stop()
