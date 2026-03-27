
import easyocr
import cv2
import numpy as np
import re
from PIL import Image
import streamlit as st

# =============================
# CARREGAR EASYOCR UMA VEZ
# =============================
@st.cache_resource
def carregar_modelo():
    return easyocr.Reader(['pt', 'en'], gpu=False)


# =============================
# LIMPEZA DE TEXTO
# =============================
def limpar_texto(texto):
    texto = texto.upper()
    texto = texto.replace(",", ".")
    return texto


# =============================
# CALCULAR POLOS AUTOMATICAMENTE
# =============================
def calcular_polos(rpm, freq):
    try:
        rpm = float(rpm)
        freq = float(freq)

        polos = round((120 * freq) / rpm)

        if polos in [2,4,6,8,10,12]:
            return polos
    except:
        pass
    return ""


# =============================
# ESTIMATIVA DO INDUZIDO
# =============================
def estimar_induzido(potencia, carcaca):

    try:
        potencia = float(potencia)
    except:
        return ""

    tabela = {
        "71": 70,
        "80": 80,
        "90": 95,
        "100": 110,
        "112": 125,
        "132": 145,
        "160": 180,
        "180": 200,
        "200": 220,
        "225": 250
    }

    if carcaca in tabela:
        return f"{tabela[carcaca]} mm (estimado)"

    if potencia <= 1:
        return "≈80 mm"
    elif potencia <= 5:
        return "≈120 mm"
    elif potencia <= 15:
        return "≈180 mm"
    else:
        return "≈250 mm"


# =============================
# EXTRAIR DADOS DA PLACA
# =============================
def extrair_dados(texto):

    dados = {}

    texto = limpar_texto(texto)

    # ---------- MARCA ----------
    for marca in ["WEG","SIEMENS","ABB","SEW","VOGES","SCHNEIDER"]:
        if marca in texto:
            dados["Marca"] = marca

    # ---------- CARCAÇA ----------
    carcaca = re.search(r'\b(63|71|80|90|100|112|132|160|180|200|225)\b', texto)
    if carcaca:
        dados["Carcaça"] = carcaca.group(1)

    # ---------- POTÊNCIA ----------
    pot = re.search(r'(\d+\.?\d*)\s?(KW|CV|HP)', texto)
    if pot:
        dados["Potência"] = pot.group(1)
        dados["Unidade"] = pot.group(2)

    # ---------- TENSÃO ----------
    tensoes = re.findall(r'\b(110|127|220|254|380|440|460|660|760)\b', texto)
    if tensoes:
        dados["Tensão"] = " / ".join(sorted(set(tensoes)))

    # ---------- CORRENTE ----------
    corrente = re.search(r'(\d+\.?\d*)\s?A\b', texto)
    if corrente:
        dados["Corrente"] = corrente.group(1)

    # ---------- FREQUÊNCIA ----------
    freq = re.search(r'(50|60)\s?HZ', texto)
    if freq:
        dados["Frequência"] = freq.group(1)

    # ---------- RPM ----------
    rpm = re.search(r'(\d{3,4})\s?RPM', texto)
    if rpm:
        dados["Rotação"] = rpm.group(1)

    # ---------- FP ----------
    fp = re.search(r'(0\.\d{2})\s?COS', texto)
    if fp:
        dados["Fator de potência"] = fp.group(1)

    # ---------- FS ----------
    fs = re.search(r'(1\.\d{1,2})\s?SF', texto)
    if fs:
        dados["Fator de Serviço"] = fs.group(1)

    # ---------- IP ----------
    ip = re.search(r'IP\s?(\d{2})', texto)
    if ip:
        dados["IP"] = "IP"+ip.group(1)

    # ---------- ISOLAMENTO ----------
    iso = re.search(r'CLASS\s?([A-F-H])', texto)
    if iso:
        dados["Isolamento"] = iso.group(1)

    # ---------- LIGAÇÃO ----------
    if "Δ" in texto or "DELTA" in texto:
        dados["Ligação"] = "Δ"
    if "Y" in texto or "STAR" in texto:
        dados["Ligação"] = dados.get("Ligação","")+" / Y"

    # ---------- PESO ----------
    peso = re.search(r'(\d+\.?\d*)\s?KG', texto)
    if peso:
        dados["Peso"] = peso.group(1)

    # ---------- REFRIGERAÇÃO ----------
    if "TFVE" in texto:
        dados["Refrigeração"] = "TFVE"
    if "IC411" in texto:
        dados["Refrigeração"] = "IC411"

    # ---------- POLOS AUTOMÁTICO ----------
    if "Rotação" in dados and "Frequência" in dados:
        dados["Polos"] = calcular_polos(
            dados["Rotação"],
            dados["Frequência"]
        )

    # ---------- INDUZIDO ESTIMADO ----------
    dados["Induzido estimado"] = estimar_induzido(
        dados.get("Potência",""),
        dados.get("Carcaça","")
    )

    return dados


# =============================
# FUNÇÃO PRINCIPAL OCR
# =============================
def ler_placa_motor(imagem_input):

    reader = carregar_modelo()

    if isinstance(imagem_input, str):
        imagem = cv2.imread(imagem_input)
    else:
        imagem = np.array(Image.open(imagem_input))

    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    resultado = reader.readtext(gray)

    texto_total = " ".join([r[1] for r in resultado])

    dados = extrair_dados(texto_total)

    return dados
