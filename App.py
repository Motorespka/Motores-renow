import streamlit as st

# ================= CONFIGURAÇÃO =================

st.set_page_config(
    page_title="Moto-Renow",
    layout="wide"
)

# ================= IMPORTS DAS PÁGINAS =================

from page.cadastro import show as cadastro_page
from page.consulta import show as consulta_page
from page.calculadora import show as calculadora_page

# ================= LOGIN =================

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

# ================= SISTEMA =================

st.title("⚙️ Moto-Renow")

menu = st.sidebar.radio(
    "Menu",
    ["Cadastro", "Consulta", "Calculadora"]
)

# ================= NAVEGAÇÃO =================

if menu == "Cadastro":
    cadastro_page()

elif menu == "Consulta":
    consulta_page()

elif menu == "Calculadora":
    calculadora_page()
