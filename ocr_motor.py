import easyocr
import cv2
import re
import numpy as np
import streamlit as st
from PIL import Image

# =========================
# 🔧 1. CARREGAR MODELO
# =========================
@st.cache_resource
def carregar_modelo():
    """Carrega o modelo EasyOCR apenas uma vez"""
    return easyocr.Reader(['pt', 'en'], gpu=False)

# =========================
# 🔎 2. EXTRAIR DADOS DO TEXTO
# =========================
def extrair_dados_especificos(texto):
    """
    Extrai os dados do motor de um texto bruto.
    Flexível para diferentes formatos de placas.
    """
    texto_limpo = " ".join(texto) if isinstance(texto, list) else texto

    dados = {
        "Marca": "",
        "Tensão": "",
        "Potência": "",
        "Rotação": "",
        "Frequência": "",
        "Corrente": ""
    }

    # ===== 1. MARCA =====
    marcas = ["WEG", "SIEMENS", "VOGES"]
    for m in marcas:
        if m.upper() in texto_limpo.upper():
            dados["Marca"] = m
            break

    # ===== 2. TENSÃO =====
    tensoes = re.findall(r'\b(110|127|220|380|440|460|760)\b', texto_limpo)
    if tensoes:
        dados["Tensão"] = " / ".join(sorted(list(set(tensoes))))

    # ===== 3. ROTAÇÃO =====
    rpm_match = re.search(r'(\d{3,4})\s?(?:RPM|min|MIN)?', texto_limpo, re.IGNORECASE)
    if rpm_match:
        dados["Rotação"] = rpm_match.group(1)
    else:
        rpms_comuns = re.findall(r'\b(8[0-9]{2}|11[0-9]{2}|17[0-9]{2}|34[0-9]{2}|35[0-9]{2})\b', texto_limpo)
        if rpms_comuns:
            dados["Rotação"] = rpms_comuns[0]

    # ===== 4. FREQUÊNCIA =====
    freq = re.search(r'(50|60)\s?Hz', texto_limpo, re.IGNORECASE)
    if freq:
        dados["Frequência"] = freq.group(1)

    # ===== 5. POTÊNCIA =====
    pot = re.search(r'(\d+[\.,]?\d*)\s?(?:kW|HP|CV|cv)', texto_limpo, re.IGNORECASE)
    if pot:
        dados["Potência"] = pot.group(1).replace(",", ".")

    # ===== 6. CORRENTE =====
    corrente = re.search(r'(\d+[\.,]?\d*)\s?A\b', texto_limpo, re.IGNORECASE)
    if corrente:
        dados["Corrente"] = corrente.group(1).replace(",", ".")

    return dados

# =========================
# 🔧 3. FUNÇÃO PRINCIPAL
# =========================
def ler_placa_motor(imagem_input):
    """
    Recebe caminho de imagem ou objeto PIL e retorna dicionário com dados do motor.
    """

    reader = carregar_modelo()

    # converte para np.ndarray se necessário
    if isinstance(imagem_input, str):
        imagem_input = cv2.imread(imagem_input)
    elif not isinstance(imagem_input, np.ndarray):
        imagem_input = np.array(imagem_input)

    # converte para grayscale
    if len(imagem_input.shape) == 3:
        gray = cv2.cvtColor(imagem_input, cv2.COLOR_BGR2GRAY)
    else:
        gray = imagem_input

    # lê com OCR
    resultado = reader.readtext(gray)

    # junta em texto único
    texto_total = " ".join([res[1] for res in resultado])

    # retorna dicionário processado
    dados_extraidos = extrair_dados_especificos(texto_total)
    return dados_extraidos

# =========================
# 🔬 4. TESTE LOCAL
# =========================
if __name__ == "__main__":
    import streamlit as st
    st.title("Teste de OCR Local")
    arquivo = st.file_uploader("Suba uma placa", type=['jpg', 'png'])
    if arquivo:
        img = Image.open(arquivo)
        st.image(img)
        res = ler_placa_motor(img)
        st.write("Dados extraídos pelo OCR:")
        st.json(res)
