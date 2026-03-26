import easyocr
import cv2
import re
import numpy as np
from PIL import Image
import streamlit as st

@st.cache_resource
def carregar_modelo():
    """Carrega EasyOCR uma vez"""
    return easyocr.Reader(['pt', 'en'], gpu=False)

def extrair_dados_especificos(texto):
    texto_limpo = " ".join(texto) if isinstance(texto, list) else texto
    dados = {"Marca": "", "Tensão": "", "Potência": "", "Rotação": "", "Frequência": "", "Corrente": ""}

    # Marca
    for m in ["WEG", "SIEMENS", "VOGES"]:
        if m.upper() in texto_limpo.upper():
            dados["Marca"] = m
            break

    # Tensão
    tensoes = re.findall(r'\b(110|127|220|380|440|460|760)\b', texto_limpo)
    if tensoes:
        dados["Tensão"] = " / ".join(sorted(set(tensoes)))

    # Rotação
    rpm = re.search(r'(\d{3,4})\s?(?:RPM|min|MIN)?', texto_limpo, re.IGNORECASE)
    if rpm: dados["Rotação"] = rpm.group(1)

    # Frequência
    freq = re.search(r'(50|60)\s?Hz', texto_limpo, re.IGNORECASE)
    if freq: dados["Frequência"] = freq.group(1)

    # Potência
    pot = re.search(r'(\d+[\.,]?\d*)\s?(?:kW|HP|CV|cv)', texto_limpo, re.IGNORECASE)
    if pot: dados["Potência"] = pot.group(1).replace(",", ".")

    # Corrente
    amp = re.search(r'(\d+[\.,]?\d*)\s?A\b', texto_limpo, re.IGNORECASE)
    if amp: dados["Corrente"] = amp.group(1).replace(",", ".")

    return dados

def ler_placa_motor(imagem_input):
    reader = carregar_modelo()
    if isinstance(imagem_input, str):
        imagem_input = cv2.imread(imagem_input)
    elif not isinstance(imagem_input, np.ndarray):
        imagem_input = np.array(imagem_input)

    if len(imagem_input.shape) == 3:
        gray = cv2.cvtColor(imagem_input, cv2.COLOR_BGR2GRAY)
    else:
        gray = imagem_input

    resultado = reader.readtext(gray)
    texto_total = " ".join([res[1] for res in resultado])
    return extrair_dados_especificos(texto_total)
