import streamlit as st

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Moto-Renow",
    layout="wide"
)

# ---------------- LOGIN ----------------
def check_login():

    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:

        st.title("🔐 Login Moto-Renow")

        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):

            if (
                usuario == st.secrets["login"]["usuario"]
                and senha == st.secrets["login"]["senha"]
            ):
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

        st.stop()

check_login()

# ---------------- APP ----------------
st.title("Moto-Renow")

menu = st.sidebar.selectbox(
    "Menu",
    ["Cadastro", "Consulta", "Calculadora"]
)

if menu == "Cadastro":
    from pages.cadastro import show
    show()

elif menu == "Consulta":
    from pages.consulta import show
    show()

elif menu == "Calculadora":
    from pages.calculadora import show
    show()
