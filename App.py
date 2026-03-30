import streamlit as st
import importlib

# ===============================
# CONFIGURAÇÃO DO APP
# ===============================
st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# ===============================
# LOGIN PROFISSIONAL
# ===============================
from auth.login import check_login
from auth.logout import botao_logout

check_login()

# ===============================
# INTERFACE PRINCIPAL
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
# CARREGAMENTO SEGURO DAS PÁGINAS
# ===============================
def carregar_pagina(modulo, nome):

    try:
        page = importlib.import_module(modulo)

        if hasattr(page, "show") and callable(page.show):
            page.show()
        else:
            st.error(f"A página '{nome}' precisa ter uma função show()")

    except ModuleNotFoundError:
        st.error(f"Página '{nome}' não encontrada.")

    except Exception as e:
        st.error(f"Erro ao carregar {nome}")
        st.exception(e)


# ===============================
# ROTEAMENTO
# ===============================
paginas = {
    "Cadastro": "pages.cadastro",
    "Consulta": "pages.consulta",
    "Calculadora": "pages.calculadora",
    "Rebobinador": "pages.rebobinador",
}

carregar_pagina(paginas[menu], menu)
