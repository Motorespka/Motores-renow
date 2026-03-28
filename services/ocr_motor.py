# ocr_motor.py
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
    """Cria e retorna o leitor EasyOCR (português + inglês)"""
    return easyocr.Reader(['pt', 'en'], gpu=False)

# =============================
# LIMPAR TEXTO
# =============================
def limpar_texto(texto):
    """Remove acentos e coloca tudo em maiúsculo"""
    texto = texto.upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    return texto

# =============================
# FUNÇÃO PRINCIPAL OCR
# =============================
def ler_placa_motor(imagem_input):
    reader = carregar_modelo()

    # =============================
    # Converte input em imagem OpenCV
    # =============================
    try:
        # Se for arquivo do Streamlit (camera_input ou file_uploader)
        if hasattr(imagem_input, "read"):
            imagem = Image.open(imagem_input)
        else:
            imagem = Image.open(imagem_input)

        # Converte para array numpy
        imagem_cv = np.array(imagem)

        # Converte canais corretamente
        if len(imagem_cv.shape) == 3:
            if imagem_cv.shape[2] == 3:
                imagem_cv = cv2.cvtColor(imagem_cv, cv2.COLOR_RGB2BGR)
            elif imagem_cv.shape[2] == 4:
                imagem_cv = cv2.cvtColor(imagem_cv, cv2.COLOR_RGBA2BGR)

        # Converte para grayscale
        gray = cv2.cvtColor(imagem_cv, cv2.COLOR_BGR2GRAY)

        # Threshold para melhorar contraste
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")
        return {}

    # =============================
    # OCR com EasyOCR
    # =============================
    resultado = reader.readtext(thresh)
    texto_total = " ".join([r[1] for r in resultado])
    texto_total = limpar_texto(texto_total)

    # =============================
    # Mapeamento para campos do motor
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

    # =============================
    # BUSCAS SIMPLES COM REGEX
    # =============================
    # Marca
    for marca in ["WEG","SIEMENS","ABB","SEW","VOGES","SCHNEIDER"]:
        if marca in texto_total:
            dados["marca"] = marca

    # Carcaça
    carcaca = re.search(r'\b(63|71|80|90|100|112|132|160|180|200|225)\b', texto_total)
    if carcaca:
        dados["carcaca"] = carcaca.group(1)

    # Potência
    pot = re.search(r'(\d+\.?\d*)\s?(KW|CV|HP)', texto_total)
    if pot:
        dados["potencia"] = pot.group(1)

    # Tensão
    tensoes = re.findall(r'\b(110|127|220|254|380|440|460|660|760)\b', texto_total)
    if tensoes:
        dados["tensao"] = " / ".join(sorted(set(tensoes)))

    # Corrente
    corrente = re.search(r'(\d+\.?\d*)\s?A\b', texto_total)
    if corrente:
        dados["corrente"] = corrente.group(1)

    # Frequência
    freq = re.search(r'(50|60)\s?HZ', texto_total)
    if freq:
        dados["frequencia"] = freq.group(1)

    # RPM
    rpm = re.search(r'(\d{3,5})\s?RPM', texto_total)
    if rpm:
        dados["rpm"] = rpm.group(1)

    # Fator de potência
    fp = re.search(r'(0\.\d{1,2})\s?COS', texto_total)
    if fp:
        dados["fp"] = fp.group(1)

    # IP
    ip = re.search(r'IP\s?(\d{2})', texto_total)
    if ip:
        dados["ip"] = "IP"+ip.group(1)

    # Isolamento
    iso = re.search(r'CLASS\s?([A-F-H])', texto_total)
    if iso:
        dados["isolacao"] = iso.group(1)

    # Ligação
    if "DELTA" in texto_total or "Δ" in texto_total:
        dados["ligacao"] = "Δ"
    if "Y" in texto_total or "STAR" in texto_total:
        if dados["ligacao"]:
            dados["ligacao"] += " / Y"
        else:
            dados["ligacao"] = "Y"

    # Peso
    peso = re.search(r'(\d+\.?\d*)\s?KG', texto_total)
    if peso:
        dados["peso"] = peso.group(1)

    # Retorna todos os dados
    return dados
