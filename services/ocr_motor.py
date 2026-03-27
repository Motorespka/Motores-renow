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
    texto = texto.replace("KW.", "KW")
    texto = texto.replace("CV.", "CV")
    # Correções comuns OCR
    texto = texto.replace("O", "0").replace("I", "1").replace("L", "1")
    return texto


# =============================
# CALCULAR POLOS AUTOMATICAMENTE
# =============================
def calcular_polos(rpm, freq):
    try:
        rpm = float(rpm)
        freq = float(freq)
        polos = round((120 * freq) / rpm)
        if polos in [2, 4, 6, 8, 10, 12]:
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
# FUNÇÃO AUXILIAR: CORRIGE NÚMEROS E VALORES
# =============================
def corrigir_numero(valor, minimo=None, maximo=None):
    if not valor:
        return "N/A"
    # mantém apenas números
    numero = re.sub(r"[^\d\.]", "", str(valor))
    try:
        numero = float(numero)
        if minimo is not None and numero < minimo:
            return "N/A"
        if maximo is not None and numero > maximo:
            return "N/A"
        return str(int(numero)) if numero.is_integer() else str(numero)
    except:
        return "N/A"


# =============================
# EXTRAIR DADOS DA PLACA
# =============================
def extrair_dados(texto):
    dados = {}
    texto = limpar_texto(texto)

    # ---------- MARCA ----------
    for marca in ["WEG", "SIEMENS", "ABB", "SEW", "VOGES", "SCHNEIDER"]:
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
    rpm = re.search(r'(\d{3,5})\s?RPM', texto)
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

    # ---------- VALIDAR NUMÉRICOS ----------
    dados["Rotação"] = corrigir_numero(dados.get("Rotação"), 800, 3800)
    dados["Frequência"] = corrigir_numero(dados.get("Frequência"), 50, 60)
    dados["Tensão"] = corrigir_numero(dados.get("Tensão"), 110, 1000)
    dados["Corrente"] = corrigir_numero(dados.get("Corrente"), 0.1, 500)
    dados["Peso"] = corrigir_numero(dados.get("Peso"), 0.1, 10000)

    return dados


# =============================
# FUNÇÃO PRINCIPAL OCR
# =============================
def ler_placa_motor(imagem_input):
    reader = carregar_modelo()

    # Ler imagem do arquivo ou do uploader
    if isinstance(imagem_input, str):
        imagem = cv2.imread(imagem_input)
    else:
        imagem = np.array(Image.open(imagem_input))

    gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

    # OCR
    resultado = reader.readtext(gray)
    texto_total = " ".join([r[1] for r in resultado])

    # Extrair dados da placa
    dados = extrair_dados(texto_total)

    return dados
