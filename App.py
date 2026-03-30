import streamlit as st
import importlib

from auth.login import check_login
from auth.logout import botao_logout

# ================= CONFIG =================

st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# ================= LOGIN =================

check_login()

# ================= ESTILO =================

st.markdown("""
<style>

.block-container{
    padding-top:2rem;
}

.stButton>button{
    border-radius:10px;
    transition:0.3s;
}

.stButton>button:hover{
    transform:scale(1.05);
}

</style>
""", unsafe_allow_html=True)

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
    botao_logout()

# ================= ROUTER =================

def carregar_pagina(nome):

    try:
        modulo = f"page.{nome}"   # 👈 AQUI ESTÁ A MUDANÇA
        page = importlib.import_module(modulo)

        if hasattr(page, "show"):
            page.show()
        else:
            st.error(f"{nome} não possui função show()")

    except Exception as e:
        st.error(f"Erro ao carregar {nome}")
        st.exception(e)

carregar_pagina(menu)
