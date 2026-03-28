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
    return easyocr.Reader(['pt', 'en'], gpu=False)

# =============================
# LIMPAR TEXTO
# =============================
def limpar_texto(texto):
    if not texto: return ""
    texto = texto.upper()
    texto = unicodedata.normalize('NFKD', texto)
    return texto.encode('ASCII', 'ignore').decode('ASCII')

# =============================
# FUNÇÃO PRINCIPAL OCR
# =============================
def ler_placa_motor(imagem_input):
    reader = carregar_modelo()

    try:
        # CORREÇÃO CRÍTICA: Identifica o tipo de entrada para evitar erro .read()
        if isinstance(imagem_input, np.ndarray):
            imagem_cv = imagem_input.copy()
        else:
            # Se for objeto do Streamlit, abrimos com PIL e convertemos para Numpy
            imagem_pil = Image.open(imagem_input)
            imagem_cv = np.array(imagem_pil)

        # Converte cores se necessário (Streamlit/PIL costumam usar RGB)
        if len(imagem_cv.shape) == 3:
            if imagem_cv.shape[2] == 3:
                imagem_cv = cv2.cvtColor(imagem_cv, cv2.COLOR_RGB2BGR)
            elif imagem_cv.shape[2] == 4:
                imagem_cv = cv2.cvtColor(imagem_cv, cv2.COLOR_RGBA2BGR)

        # Pré-processamento básico
        gray = cv2.cvtColor(imagem_cv, cv2.COLOR_BGR2GRAY)
        
    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")
        return {}

    # Executa o OCR
    resultado = reader.readtext(gray)
    texto_total = " ".join([r[1] for r in resultado])
    texto_total = limpar_texto(texto_total)

    # Dicionário de resultados
    dados = {key: "" for key in ["marca", "modelo", "potencia", "tensao", "corrente", "rpm", "frequencia", "fp", "carcaca", "ip", "isolacao", "regime", "rolamento_dianteiro", "rolamento_traseiro", "peso", "diametro_eixo", "comprimento_pacote", "numero_ranhuras", "ligacao", "fabricacao"]}

    # --- BUSCAS REGEX ---
    # Marcas
    for m in ["WEG", "SIEMENS", "ABB", "SEW", "VOGES", "SCHNEIDER", "KOHLBACH"]:
        if m in texto_total:
            dados["marca"] = m
            break

    # Carcaça
    carcaca = re.search(r'\b(63|71|80|90|100|112|132|160|180|200|225)\b', texto_total)
    if carcaca: dados["carcaca"] = carcaca.group(1)

    # Potência
    pot = re.search(r'(\d+[.,]?\d*)\s?(KW|CV|HP)', texto_total)
    if pot: dados["potencia"] = f"{pot.group(1)} {pot.group(2)}"

    # Tensão
    tensoes = re.findall(r'\b(110|127|220|254|380|440|460|660|760)\b', texto_total)
    if tensoes: dados["tensao"] = " / ".join(sorted(set(tensoes)))

    # RPM
    rpm = re.search(r'(\d{3,5})\s?RPM', texto_total)
    if rpm: dados["rpm"] = rpm.group(1)

    # Frequência
    freq = re.search(r'(50|60)\s?HZ', texto_total)
    if freq: dados["frequencia"] = freq.group(1)

    return dados
