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
    if not texto:
        return ""
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
    # Converte input em imagem OpenCV (CORRIGIDO)
    # =============================
    try:
        # Se for um array do numpy (OpenCV), usamos direto
        if isinstance(imagem_input, np.ndarray):
            imagem_cv = imagem_input.copy()
            
        # Se for um arquivo do Streamlit (com método .read) ou caminho de arquivo
        else:
            imagem_pil = Image.open(imagem_input)
            imagem_cv = np.array(imagem_pil)

        # Garante que a imagem está no formato BGR para o OpenCV
        if len(imagem_cv.shape) == 3:
            if imagem_cv.shape[2] == 3:
                # Se veio do PIL, está em RGB, converte para BGR
                imagem_cv = cv2.cvtColor(imagem_cv, cv2.COLOR_RGB2BGR)
            elif imagem_cv.shape[2] == 4:
                # Se tiver canal alpha (RGBA), converte para BGR
                imagem_cv = cv2.cvtColor(imagem_cv, cv2.COLOR_RGBA2BGR)

        # Pré-processamento para melhorar o OCR
        gray = cv2.cvtColor(imagem_cv, cv2.COLOR_BGR2GRAY)
        
        # Aumentar a escala pode ajudar se a placa estiver longe
        # gray = cv2.resize(gray, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)

        # Threshold para melhorar contraste (Otsu ajuda em fotos com luz variada)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")
        return {}

    # =============================
    # OCR com EasyOCR
    # =============================
    # Passamos a imagem em escala de cinza (gray) ou binarizada (thresh)
    resultado = reader.readtext(gray) 
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
    marcas_conhecidas = ["WEG", "SIEMENS", "ABB", "SEW", "VOGES", "SCHNEIDER", "KOHLBACH", "EBERLE"]
    for marca in marcas_conhecidas:
        if marca in texto_total:
            dados["marca"] = marca
            break

    # Carcaça
    carcaca = re.search(r'\b(63|71|80|90|100|112|132|160|180|200|225|250|280|315)\b', texto_total)
    if carcaca:
        dados["carcaca"] = carcaca.group(1)

    # Potência (KW, CV ou HP)
    pot = re.search(r'(\d+[.,]?\d*)\s?(KW|CV|HP)', texto_total)
    if pot:
        dados["potencia"] = pot.group(1) + " " + pot.group(2)

    # Tensão
    tensoes = re.findall(r'\b(110|127|220|254|380|440|460|660|760)\b', texto_total)
    if tensoes:
        dados["tensao"] = " / ".join(sorted(set(tensoes)))

    # Corrente
    corrente = re.search(r'(\d+[.,]?\d*)\s?A\b', texto_total)
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

    # Fator de potência (cos phi)
    fp = re.search(r'(0[.,]\d{1,2})\b', texto_total)
    if fp and ("COS" in texto_total or "PF" in texto_total):
        dados["fp"] = fp.group(1)

    # IP (Grau de Proteção)
    ip = re.search(r'IP\s?(\d{2})', texto_total)
    if ip:
        dados["ip"] = "IP" + ip.group(1)

    # Isolamento
    iso = re.search(r'ISOL\s?([A-F-H])|CLASS\s?([A-F-H])', texto_total)
    if iso:
        dados["isolacao"] = iso.group(1) if iso.group(1) else iso.group(2)

    # Ligação
    if any(x in texto_total for x in ["DELTA", "Δ", "D"]):
        dados["ligacao"] = "Δ"
    if any(x in texto_total for x in ["Y", "STAR", "ESTRELA"]):
        if dados["ligacao"]:
            dados["ligacao"] += " / Y"
        else:
            dados["ligacao"] = "Y"

    # Peso
    peso = re.search(r'(\d+[.,]?\d*)\s?KG', texto_total)
    if peso:
        dados["peso"] = peso.group(1)

    return dados
