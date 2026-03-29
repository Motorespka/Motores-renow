import easyocr
import cv2
import numpy as np
from PIL import Image, ExifTags
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
    if not texto:
        return ""

    texto = texto.upper()
    texto = unicodedata.normalize('NFKD', texto)
    return texto.encode('ASCII', 'ignore').decode('ASCII')


# =============================
# CORRIGIR ORIENTAÇÃO CELULAR
# =============================
def corrigir_orientacao(imagem_input):

    img = Image.open(imagem_input)

    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break

        exif = img._getexif()

        if exif is not None:
            orientacao = exif.get(orientation)

            if orientacao == 3:
                img = img.rotate(180, expand=True)
            elif orientacao == 6:
                img = img.rotate(270, expand=True)
            elif orientacao == 8:
                img = img.rotate(90, expand=True)

    except:
        pass

    return np.array(img)


# =============================
# PREPARAR IMAGEM PARA OCR
# (FUNCIONA COM FOTO E PRINT)
# =============================
def preparar_para_ocr(imagem_cv):

    # garante tamanho ideal
    h, w = imagem_cv.shape[:2]
    if max(h, w) > 1600:
        escala = 1600 / max(h, w)
        imagem_cv = cv2.resize(
            imagem_cv,
            (int(w * escala), int(h * escala))
        )

    # converte RGB/RGBA → BGR
    if len(imagem_cv.shape) == 3:
        if imagem_cv.shape[2] == 3:
            imagem_cv = cv2.cvtColor(imagem_cv, cv2.COLOR_RGB2BGR)
        elif imagem_cv.shape[2] == 4:
            imagem_cv = cv2.cvtColor(imagem_cv, cv2.COLOR_RGBA2BGR)

    # escala de cinza
    gray = cv2.cvtColor(imagem_cv, cv2.COLOR_BGR2GRAY)

    # melhora contraste
    gray = cv2.equalizeHist(gray)

    # remove ruído
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # binarização (segredo do OCR)
    _, thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return thresh


# =============================
# FUNÇÃO PRINCIPAL OCR
# =============================
def ler_placa_motor(imagem_input):

    reader = carregar_modelo()

    try:
        # Corrige orientação
        imagem_cv = corrigir_orientacao(imagem_input)

        # Pré-processa (foto + screenshot)
        imagem_processada = preparar_para_ocr(imagem_cv)

        # mostra imagem tratada (debug)
        st.image(imagem_processada, caption="Imagem tratada OCR")

    except Exception as e:
        st.error(f"Erro ao processar imagem: {e}")
        return {}

    # =============================
    # EXECUTA OCR
    # =============================
    resultado = reader.readtext(imagem_processada)

    texto_total = " ".join([r[1] for r in resultado])
    texto_total = limpar_texto(texto_total)

    # =============================
    # DICIONÁRIO RESULTADO
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
        "fabricacao": "",
    }

    # =============================
    # REGEX INTELIGENTE
    # =============================

    # Marcas
    for m in ["WEG", "SIEMENS", "ABB", "SEW", "VOGES", "SCHNEIDER", "KOHLBACH"]:
        if m in texto_total:
            dados["marca"] = m
            break

    # Carcaça
    carcaca = re.search(r'\b(63|71|80|90|100|112|132|160|180|200|225)\b', texto_total)
    if carcaca:
        dados["carcaca"] = carcaca.group(1)

    # Potência
    pot = re.search(r'(\d+[.,]?\d*)\s?(KW|CV|HP)', texto_total)
    if pot:
        dados["potencia"] = f"{pot.group(1)} {pot.group(2)}"

    # Tensão
    tensoes = re.findall(r'\b(110|127|220|254|380|440|460|660|760)\b', texto_total)
    if tensoes:
        dados["tensao"] = " / ".join(sorted(set(tensoes)))

    # RPM
    rpm = re.search(r'(\d{3,5})\s?RPM', texto_total)
    if rpm:
        dados["rpm"] = rpm.group(1)

    # Frequência
    freq = re.search(r'(50|60)\s?HZ', texto_total)
    if freq:
        dados["frequencia"] = freq.group(1)

    return dados
