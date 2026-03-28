# services/ocr_motor.py
import requests
from PIL import Image
import io
import re
import unicodedata
import streamlit as st

# =============================
# LIMPAR TEXTO
# =============================
def limpar_texto(texto):
    texto = texto.upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    return texto

# =============================
# FUNÇÃO PRINCIPAL OCR ONLINE
# =============================
def ler_placa_motor(imagem_input):
    """
    Recebe o arquivo de imagem do Streamlit e retorna um dicionário com os campos do motor.
    """

    # =============================
    # PREPARA A IMAGEM PARA ENVIO
    # =============================
    if isinstance(imagem_input, str):
        # caminho local
        with open(imagem_input, "rb") as f:
            img_bytes = f.read()
    else:
        # arquivo do uploader
        img_bytes = imagem_input.read()

    # =============================
    # CHAMADA API OCR.Space
    # =============================
    api_key = "helloworld"  # chave gratuita de teste
    url = "https://api.ocr.space/parse/image"

    payload = {
        'isOverlayRequired': False,
        'apikey': api_key,
        'language': 'por',
    }
    files = {'filename': img_bytes}

    try:
        response = requests.post(url, data=payload, files=files)
        result = response.json()
        if result['OCRExitCode'] != 1:
            st.warning("⚠️ OCR não conseguiu ler a imagem")
            texto_total = ""
        else:
            texto_total = result['ParsedResults'][0]['ParsedText']
    except Exception as e:
        st.error(f"Erro OCR: {e}")
        texto_total = ""

    texto_total = limpar_texto(texto_total)

    # =============================
    # DICIONÁRIO PADRÃO
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
    # EXTRAÇÃO COM REGEX
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
    fp = re.search(r'(0\.\d{2})\s?COS', texto_total)
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

    return dados
