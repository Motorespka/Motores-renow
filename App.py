import streamlit as st
import importlib

from auth.login import check_login

# CONFIG
st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# LOGIN
check_login()

st.title("⚙️ Moto-Renow")

menu = st.selectbox(
    "Menu",
    ["Cadastro", "Consulta", "Calculadora"]
)

def carregar_pagina(modulo, nome):

    try:
        page = importlib.import_module(modulo)

        if hasattr(page, "show"):
            page.show()
        else:
            st.error(f"{nome} não possui show()")

    except Exception as e:
        st.error(f"Erro ao carregar {nome}")
        st.exception(e)

if menu == "Cadastro":
    carregar_pagina("pages.cadastro", "Cadastro")

elif menu == "Consulta":
    carregar_pagina("pages.consulta", "Consulta")

elif menu == "Calculadora":
    carregar_pagina("pages.calculadora", "Calculadora")
