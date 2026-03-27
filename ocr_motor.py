
import easyocr
import cv2
import re
import numpy as np
from PIL import Image
import streamlit as st


# ======================================
# CARREGAR MODELO UMA ÚNICA VEZ
# ======================================
@st.cache_resource
def carregar_modelo():
    return easyocr.Reader(['pt', 'en'], gpu=False)


# ======================================
# MELHORAR IMAGEM PARA OCR
# ======================================
def preprocessar_imagem(img):

    # escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # aumentar contraste
    gray = cv2.equalizeHist(gray)

    # remover ruído
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # binarização adaptativa
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    return thresh


# ======================================
# EXTRAÇÃO INTELIGENTE DOS DADOS
# ======================================
def extrair_dados_especificos(texto_total):

    texto = texto_total.upper()

    dados = {
        "Marca": "",
        "Modelo": "",
        "Carcaça": "",
        "Potência": "",
        "Tensão": "",
        "Corrente": "",
        "Rotação": "",
        "Frequência": "",
        "Polos": 4,
        "IP": "",
        "Isolamento": "",
        "Fator de potência": "",
        "Fator de Serviço": ""
    }

    # ======================
    # MARCA
    # ======================
    for marca in ["WEG", "SIEMENS", "VOGES", "ABB", "SEW"]:
        if marca in texto:
            dados["Marca"] = marca
            break

    # ======================
    # MODELO
    # ======================
    modelo = re.search(r'MOD(?:EL)?[:\s\-]*([A-Z0-9\-]+)', texto)
    if modelo:
        dados["Modelo"] = modelo.group(1)

    # ======================
    # CARCAÇA
    # ======================
    carcaca = re.search(r'\b(\d{2,3}[A-Z]?)\b', texto)
    if carcaca:
        dados["Carcaça"] = carcaca.group(1)

    # ======================
    # POTÊNCIA
    # ======================
    pot = re.search(r'(\d+[\.,]?\d*)\s?(KW|CV|HP)', texto)
    if pot:
        dados["Potência"] = pot.group(1).replace(",", ".")

    # ======================
    # TENSÃO
    # ======================
    tensoes = re.findall(r'\b(110|127|220|380|440|460|760)\b', texto)
    if tensoes:
        dados["Tensão"] = " / ".join(sorted(set(tensoes)))

    # ======================
    # CORRENTE
    # ======================
    amp = re.search(r'(\d+[\.,]?\d*)\s?A\b', texto)
    if amp:
        dados["Corrente"] = amp.group(1).replace(",", ".")

    # ======================
    # ROTAÇÃO
    # ======================
    rpm = re.search(r'(\d{3,4})\s?(RPM|MIN)', texto)
    if rpm:
        dados["Rotação"] = rpm.group(1)

    # ======================
    # FREQUÊNCIA
    # ======================
    freq = re.search(r'(50|60)\s?HZ', texto)
    if freq:
        dados["Frequência"] = freq.group(1)

    # ======================
    # POLOS
    # ======================
    polos = re.search(r'(\d)\s?P', texto)
    if polos:
        dados["Polos"] = int(polos.group(1))

    # ======================
    # IP
    # ======================
    ip = re.search(r'IP\s?(\d{2})', texto)
    if ip:
        dados["IP"] = "IP" + ip.group(1)

    # ======================
    # ISOLAMENTO
    # ======================
    iso = re.search(r'ISOL\.?\s?([A-Z])', texto)
    if iso:
        dados["Isolamento"] = iso.group(1)

    # ======================
    # FATOR POTÊNCIA
    # ======================
    fp = re.search(r'FP\s?=?\s?(\d[\.,]\d+)', texto)
    if fp:
        dados["Fator de potência"] = fp.group(1).replace(",", ".")

    # ======================
    # FATOR SERVIÇO
    # ======================
    fs = re.search(r'FS\s?=?\s?(\d[\.,]\d+)', texto)
    if fs:
        dados["Fator de Serviço"] = fs.group(1).replace(",", ".")

    return dados


# ======================================
# FUNÇÃO PRINCIPAL OCR
# ======================================
def ler_placa_motor(imagem_input):

    reader = carregar_modelo()

    # carregar imagem
    if isinstance(imagem_input, str):
        img = cv2.imread(imagem_input)
    elif isinstance(imagem_input, Image.Image):
        img = np.array(imagem_input)
    else:
        img = imagem_input

    if img is None:
        raise Exception("Imagem não carregada")

    # melhorar imagem
    processada = preprocessar_imagem(img)

    # OCR
    resultado = reader.readtext(processada)

    textos = [res[1] for res in resultado]
    texto_total = " ".join(textos)

    dados = extrair_dados_especificos(texto_total)

    return dados
