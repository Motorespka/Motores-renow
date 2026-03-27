import streamlit as st

# =====================================
# CONFIGURAÇÃO
# =====================================

st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# =====================================
# LOGIN SIMPLES
# =====================================

def login():

    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:

        st.title("🔐 Moto-Renow - Acesso Técnico")

        senha = st.text_input(
            "Digite a chave técnica",
            type="password"
        )

        if senha:
            try:
                if senha == st.secrets["APP_PASSWORD"]:
                    st.session_state.logado = True
                    st.rerun()
                else:
                    st.error("Senha incorreta")
            except Exception:
                st.error("Senha não configurada no Secrets")

        st.stop()


login()

# =====================================
# MENU PRINCIPAL
# =====================================

st.title("⚙️ Moto-Renow")

menu = st.sidebar.radio(
    "Menu",
    [
        "Cadastro",
        "Consulta",
        "Calculadora"
    ]
)

# =====================================
# CARREGAMENTO SEGURO DAS PÁGINAS
# =====================================

def carregar_pagina(modulo, nome):

    try:
        page = __import__(modulo, fromlist=["show"])
        page.show()

    except Exception as e:
        st.error(f"Erro ao carregar {nome}")
        st.exception(e)


if menu == "Cadastro":
    carregar_pagina("page.cadastro", "Cadastro")

elif menu == "Consulta":
    carregar_pagina("page.consulta", "Consulta")

elif menu == "Calculadora":
    carregar_pagina("page.calculadora", "Calculadora")
