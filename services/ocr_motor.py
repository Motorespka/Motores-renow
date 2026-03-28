import easyocr
import cv2
import numpy as np
from PIL import Image
import streamlit as st
import re
import unicodedata

# =============================
# CARREGAR EASYOCR UMA VEZ
# =============================
@st.cache_resource
def carregar_modelo():
    return easyocr.Reader(['pt', 'en'], gpu=False)

# =============================
# LIMPAR TEXTO
# =============================
def limpar_texto(texto):
    texto = texto.upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    texto = texto.replace(",", ".")  # corrige vírgulas
    return texto

# =============================
# FUNÇÃO PRINCIPAL OCR
# =============================
def ler_placa_motor(imagem_input, debug=False):
    reader = carregar_modelo()

    # Ler imagem
    if isinstance(imagem_input, str):
        imagem = cv2.imread(imagem_input)
    else:
        imagem = np.array(Image.open(imagem_input))

    # Use original ou grayscale
    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    resultado = reader.readtext(gray)
    texto_total = " ".join([r[1] for r in resultado])
    texto_total = limpar_texto(texto_total)

    if debug:
        st.write("📝 Texto detectado pelo OCR:", texto_total)

    # =============================
    # MAPEAMENTO PARA CADASTRO.PY
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
    # MARCA
    # =============================
    for marca in ["WEG", "SIEMENS", "ABB", "SEW", "VOGES", "SCHNEIDER"]:
        if marca in texto_total:
            dados["marca"] = marca

    # =============================
    # MODELO
    # =============================
    match = re.search(r"MODELO[:\s]*([A-Z0-9\-]+)", texto_total)
    if match:
        dados["modelo"] = match.group(1)

    # =============================
    # CARCAÇA
    # =============================
    match = re.search(r'\b(63|71|80|90|100|112|132|160|180|200|225)\b', texto_total)
    if match:
        dados["carcaca"] = match.group(1)

    # =============================
    # POTÊNCIA
    # =============================
    match = re.search(r'(\d+\.?\d*)\s*(KW|CV|HP)', texto_total)
    if match:
        dados["potencia"] = match.group(1)

    # =============================
    # TENSÃO
    # =============================
    tensoes = re.findall(r'\b(110|127|220|254|380|440|460|660|760)\b', texto_total)
    if tensoes:
        dados["tensao"] = " / ".join(sorted(set(tensoes)))

    # =============================
    # CORRENTE
    # =============================
    match = re.search(r'(\d+\.?\d*)\s?(A|AMP|AMPS)?\b', texto_total)
    if match:
        dados["corrente"] = match.group(1)

    # =============================
    # FREQUÊNCIA
    # =============================
    match = re.search(r'(\d{2})\s*HZ', texto_total)
    if match:
        dados["frequencia"] = match.group(1)

    # =============================
    # RPM
    # =============================
    match = re.search(r'(\d{3,5})\s?RPM', texto_total)
    if match:
        dados["rpm"] = match.group(1)

    # =============================
    # FATOR DE POTÊNCIA
    # =============================
    match = re.search(r'0\.\d{1,2}\s?COS', texto_total)
    if match:
        dados["fp"] = match.group(0).split()[0]

    # =============================
    # IP
    # =============================
    match = re.search(r'IP\s?(\d{2})', texto_total)
    if match:
        dados["ip"] = "IP" + match.group(1)

    # =============================
    # ISOLAMENTO
    # =============================
    match = re.search(r'CLASS\s?([A-F-H])', texto_total)
    if match:
        dados["isolacao"] = match.group(1)

    # =============================
    # REGIME
    # =============================
    match = re.search(r'S\d', texto_total)
    if match:
        dados["regime"] = match.group(0)

    # =============================
    # ROLAMENTOS
    # =============================
    match = re.findall(r'(\d+\.?\d*)\s?MM', texto_total)
    if match:
        if len(match) >= 1:
            dados["diametro_eixo"] = match[0]
        if len(match) >= 2:
            dados["comprimento_pacote"] = match[1]

    # =============================
    # PESO
    # =============================
    match = re.search(r'(\d+\.?\d*)\s?KG', texto_total)
    if match:
        dados["peso"] = match.group(1)

    # =============================
    # NÚMERO DE RANHURAS
    # =============================
    match = re.search(r'(\d+)\s*RANHURAS', texto_total)
    if match:
        dados["numero_ranhuras"] = match.group(1)

    # =============================
    # LIGAÇÃO
    # =============================
    if "DELTA" in texto_total or "Δ" in texto_total:
        dados["ligacao"] = "Δ"
    if "Y" in texto_total or "STAR" in texto_total:
        if dados["ligacao"]:
            dados["ligacao"] += " / Y"
        else:
            dados["ligacao"] = "Y"

    # =============================
    # FABRICAÇÃO
    # =============================
    match = re.search(r'\b(19\d{2}|20\d{2})\b', texto_total)
    if match:
        dados["fabricacao"] = match.group(0)

    return dados
