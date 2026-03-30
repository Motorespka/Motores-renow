import streamlit as st
import importlib

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# ===============================
# LOGIN
# ===============================
from auth.login import check_login
from auth.logout import botao_logout

check_login()

# ===============================
# INTERFACE
# ===============================
st.title("⚙️ Moto-Renow")

botao_logout()

# ===============================
# MENU
# ===============================
menu = st.sidebar.radio(
    "Menu",
    [
        "Cadastro",
        "Consulta",
        "Calculadora",
        "Rebobinador"
    ]
)

# ===============================
# CARREGAR PÁGINA
# ===============================
def carregar_pagina(modulo, nome):

    try:
        page = importlib.import_module(modulo)

        if hasattr(page, "show"):
            page.show()
        else:
            st.error(f"A página '{nome}' precisa ter função show()")

    except ModuleNotFoundError:
        st.error(f"Página '{nome}' não encontrada.")

    except Exception as e:
        st.error(f"Erro ao carregar {nome}")
        st.exception(e)

# ===============================
# ROTEAMENTO
# ===============================
paginas = {
    "Cadastro": "page.cadastro",
    "Consulta": "page.consulta",
    "Calculadora": "page.calculadora",
    "Rebobinador": "page.rebobinador",
}

carregar_pagina(paginas[menu], menu)
