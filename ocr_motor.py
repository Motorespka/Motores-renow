import easyocr
import cv2
import re
import numpy as np
import streamlit as st
import os
from PIL import Image

# --- FUNÇÕES DE PROCESSAMENTO (A LÓGICA) ---

@st.cache_resource
def carregar_modelo():
    return easyocr.Reader(['pt', 'en'], gpu=False)

def preprocessar_imagem(imagem_array):
    gray = cv2.cvtColor(imagem_array, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    res = clahe.apply(gray)
    _, thresh = cv2.threshold(res, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extrair_dados_especificos(texto):
    dados = {
        "Marca": "Não detectada",
        "Tensão (V)": "Não detectada",
        "Potência (kW/HP)": "Não detectada",
        "Rotação (RPM)": "Não detectada",
        "Frequência (Hz)": "Não detectada",
        "Corrente (A)": "Não detectada"
    }
    if "WEG" in texto.upper(): dados["Marca"] = "WEG"
    elif "SIEMENS" in texto.upper(): dados["Marca"] = "SIEMENS"
    elif "VOGES" in texto.upper(): dados["Marca"] = "VOGES"

    tensoes = re.findall(r'\b(220|380|440|760)\b', texto)
    if tensoes: dados["Tensão (V)"] = " / ".join(list(set(tensoes)))

    rpm = re.search(r'(\d{3,4})\s?(?:RPM|min-1|min)', texto, re.IGNORECASE)
    if rpm: dados["Rotação (RPM)"] = rpm.group(1)

    freq = re.search(r'(50|60)\s?Hz', texto, re.IGNORECASE)
    if freq: dados["Frequência (Hz)"] = freq.group(1)

    pot = re.search(r'(\d+[.,]\d+)\s?(?:kW|HP|cv)', texto, re.IGNORECASE)
    if pot: dados["Potência (kW/HP)"] = pot.group(1)

    return dados

def ler_placa_motor(imagem_input):
    reader = carregar_modelo()
    if isinstance(imagem_input, str):
        imagem_input = cv2.imread(imagem_input)
    resultado = reader.readtext(imagem_input)
    texto_total = " ".join([res[1] for res in resultado])
    return extrair_dados_especificos(texto_total)

# --- INTERFACE (SÓ RODA SE VOCÊ EXECUTAR ESTE ARQUIVO DIRETO) ---
if __name__ == "__main__":
    st.set_page_config(page_title="OCR Motor Expert", layout="centered")
    st.title("🔌 Extrator de Dados de Placa de Motor")
    arquivo = st.file_uploader("Selecione a imagem", type=['jpg', 'jpeg', 'png'])

    if arquivo:
        if not os.path.exists("temp"):
            os.makedirs("temp", exist_ok=True)
        img_pil = Image.open(arquivo)
        img_array = np.array(img_pil)
        reader = carregar_modelo()
        with st.spinner('Processando...'):
            dados_finais = ler_placa_motor(img_array)
            st.write(dados_finais)
