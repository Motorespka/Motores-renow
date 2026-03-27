import streamlit as st

st.set_page_config(
    page_title="Moto-Renow",
    layout="wide"
)

# ---------------- LOGIN SIMPLES ----------------

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🔐 Acesso Técnico")

    senha = st.text_input(
        "Digite a chave técnica",
        type="password"
    )

    if senha == st.secrets["APP_PASSWORD"]:
        st.session_state.logado = True
        st.rerun()

    st.stop()

# ---------------- SISTEMA ----------------

st.title("Moto-Renow")

menu = st.sidebar.selectbox(
    "Menu",
    ["Cadastro", "Consulta", "Calculadora"]
)

if menu == "Cadastro":
    from Page.cadastro import show
    show()

elif menu == "Consulta":
    from Page.consulta import show
    show()

elif menu == "Calculadora":
    from Page.calculadora import show
    show()
