import streamlit as st

# ---------------- CONFIGURAÇÃO ----------------

st.set_page_config(
    page_title="Moto-Renow",
    layout="wide"
)

# ---------------- LOGIN ----------------

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🔐 Moto-Renow - Acesso Técnico")

    senha = st.text_input(
        "Digite a chave técnica",
        type="password"
    )

    if senha:
        if senha == st.secrets["APP_PASSWORD"]:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta")

    st.stop()

# ---------------- SISTEMA ----------------

st.title("⚙️ Moto-Renow")

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Cadastro",
        "Consulta",
        "Calculadora"
    ]
)

# ---------------- PÁGINAS ----------------

if menu == "Cadastro":
    from page.cadastro import show
    show()

elif menu == "Consulta":
    from page.consulta import show
    show()

elif menu == "Calculadora":
    from page.calculadora import show
    show()
