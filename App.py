import streamlit as st
import importlib

# ==========================
# CONFIG
# ==========================
st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# ==========================
# LOGIN PROFISSIONAL
# ==========================
from auth.login import check_login
from auth.logout import botao_logout

check_login()

# ==========================
# INTERFACE
# ==========================
st.title("⚙️ Moto-Renow")

botao_logout()

# ==========================
# MENU LATERAL
# ==========================
menu = st.sidebar.radio(
    "menu",
    [
        "cadastro",
        "consulta",
        "calculadora",
        "rebobinador"
    ]
)

# ==========================
# CARREGAMENTO DINÂMICO
# ==========================
def carregar_pagina(nome):

    try:
        modulo = f"page.{nome}"
        pagina = importlib.import_module(modulo)

        if hasattr(pagina, "show"):
            pagina.show()
        else:
            st.error(f"{nome}.py precisa da função show()")

    except ModuleNotFoundError:
        st.error(f"Página '{nome}' não encontrada")

    except Exception as e:
        st.exception(e)

carregar_pagina(menu)
