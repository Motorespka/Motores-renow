import streamlit as st
import importlib

# ================= CONFIG =================

st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# ================= CSS =================

def carregar_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )
    except Exception as e:
        st.warning("CSS não carregado")

carregar_css()

# ================= LOGIN =================

try:
    from auth.login import check_login
    from auth.logout import botao_logout

    check_login()

except Exception as e:
    st.error("Erro no sistema de login")
    st.exception(e)
    st.stop()

# ================= SIDEBAR =================

with st.sidebar:

    st.title("⚙️ Moto-Renow")

    menu = st.radio(
        "Sistema",
        [
            "cadastro",
            "consulta",
            "calculadora"
        ]
    )

    st.divider()

    try:
        botao_logout()
    except:
        pass

# ================= ROUTER =================

def carregar_pagina(nome):

    try:
        modulo = f"page.{nome}"
        page = importlib.import_module(modulo)

        if hasattr(page, "show"):
            page.show()
        else:
            st.error(f"{nome} não possui função show()")

    except Exception as e:
        st.error(f"Erro ao carregar {nome}")
        st.exception(e)

carregar_pagina(menu)
