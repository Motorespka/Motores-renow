import streamlit as st
import importlib
from PIL import Image
import numpy as np
import cv2

# =============================
# AUMENTAR LIMITE DE UPLOAD
# =============================
# Valor em MB (ex: 1024 MB = 1 GB)
st.set_option('server.maxUploadSize', 1024)

# =============================
# FUNÇÃO PARA REDIMENSIONAR IMAGEM GRANDE
# =============================
def processar_imagem(imagem_input, max_largura=1024):
    """
    Redimensiona imagem grande mantendo proporção e converte para BGR (OpenCV)
    """
    img = Image.open(imagem_input)
    if img.width > max_largura:
        proporcao = max_largura / img.width
        nova_altura = int(img.height * proporcao)
        img = img.resize((max_largura, nova_altura))
    imagem_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return imagem_cv

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
menu = st.selectbox(
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
        # importa o módulo da página
        page = importlib.import_module(modulo)

        # verifica se existe a função show()
        if hasattr(page, "show") and callable(page.show):
            page.show()
        else:
            st.error(f"A página '{nome}' não possui a função show() definida.")

    except Exception as e:
        st.error(f"Erro ao carregar {nome}")
        st.exception(e)


if menu == "Cadastro":
    carregar_pagina("page.cadastro", "Cadastro")  

elif menu == "Consulta":
    carregar_pagina("page.consulta", "Consulta")

elif menu == "Calculadora":
    carregar_pagina("page.calculadora", "Calculadora")
