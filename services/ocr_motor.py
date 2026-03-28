import easyocr
import cv2
import numpy as np
from PIL import Image
import streamlit as st
import unicodedata
import re

# =============================
# CARREGAR EASYOCR UMA VEZ
# =============================
@st.cache_resource
def carregar_modelo():
    # idiomas: português e inglês
    return easyocr.Reader(['pt', 'en'], gpu=False)

# =============================
# LIMPAR TEXTO
# =============================
def limpar_texto(texto):
    texto = texto.upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    return texto

# =============================
# FUNÇÃO PRINCIPAL OCR
# =============================
def ler_placa_motor(imagem_input):
    reader = carregar_modelo()  # Agora existe

    # Lê imagem
    if isinstance(imagem_input, str):
        imagem = cv2.imread(imagem_input)
    else:
        imagem = np.array(Image.open(imagem_input))

    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # OCR com EasyOCR
    resultado = reader.readtext(thresh)
    texto_total = " ".join([r[1] for r in resultado])
    texto_total = limpar_texto(texto_total)

    # Normalização
    texto_total = texto_total.strip().upper()

    # =============================
    # Mapeamento para cadastro.py
    # =============================
    dados = {
        "marca": "",
        "modelo": "",
        "potencia": "",
        "tensao": "",
        "corrente": "",
        "rpm": "",
        "frequencia": "",
        "fp": "",
        "carcaca": "",
        "ip": "",
        "isolacao": "",
        "regime": "",
        "rolamento_dianteiro": "",
        "rolamento_traseiro": "",
        "peso": "",
        "diametro_eixo": "",
        "comprimento_pacote": "",
        "numero_ranhuras": "",
        "ligacao": "",
        "fabricacao": ""
    }

    # Exemplo: detectar marca
    for marca in ["WEG","SIEMENS","ABB","SEW","VOGES","SCHNEIDER"]:
        if marca in texto_total:
            dados["marca"] = marca

    return dados
