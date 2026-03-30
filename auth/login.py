import streamlit as st

def check_login():

    # cria variável de sessão
    if "logado" not in st.session_state:
        st.session_state.logado = False

    # se já estiver logado
    if st.session_state.logado:
        return

    st.title("🔐 Moto-Renow - Acesso Técnico")

    senha = st.text_input(
        "Digite a chave técnica",
        type="password",
        key="senha_login"
    )

    if st.button("Entrar"):

        try:
            if senha == st.secrets["APP_PASSWORD"]:
                st.session_state.logado = True
                st.success("Login realizado")
                st.rerun()
            else:
                st.error("Senha incorreta")

        except Exception:
            st.error("APP_PASSWORD não configurada no secrets")

    st.stop()
