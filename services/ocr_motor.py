import easyocr
import numpy as np
import cv2
import re
from services.engenharia_motor import calcular_rebobinagem


# Inicializa uma única vez
reader = easyocr.Reader(['pt', 'en'], gpu=False)


# ==========================
# PREPROCESSAMENTO
# ==========================
def preprocessar_imagem(file):

    bytes_data = np.asarray(bytearray(file.read()), dtype=np.uint8)
    img = cv2.imdecode(bytes_data, 1)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh


# ==========================
# EXTRAÇÃO TEXTO
# ==========================
def ler_texto_motor(file):

    img = preprocessar_imagem(file)

    resultado = reader.readtext(img, detail=0)

    texto = " ".join(resultado).upper()

    return texto


# ==========================
# EXTRAIR DADOS GERAIS
# ==========================
def extrair_dados_motor(texto):

    dados = {}

    if "WEG" in texto:
        dados["marca"] = "WEG"

    modelo = re.search(r"W\d{2}[A-Z]?", texto)
    if modelo:
        dados["modelo"] = modelo.group()

    rpm = re.search(r"\d{4}\s?RPM", texto)
    if rpm:
        dados["rpm"] = rpm.group()

    iso = re.search(r"ISOL.? ?([A-Z])", texto)
    if iso:
        dados["isolacao"] = iso.group(1)

    reg = re.search(r"S\d", texto)
    if reg:
        dados["regime"] = reg.group()

    tensao = re.search(r"\d{2,3}\/\d{2,3}", texto)
    if tensao:
        dados["tensao"] = tensao.group()

    corrente = re.search(r"\d+[.,]\d+\s?A", texto)
    if corrente:
        dados["corrente"] = corrente.group()

    polos = re.search(r"POLOS?\s?(\d+)", texto)
    if polos:
        dados["polos"] = polos.group(1)

    return dados


# ==========================
# FUNÇÃO PRINCIPAL
# ==========================
def ler_placa_motor(file):

    texto = ler_texto_motor(file)

    dados = extrair_dados_motor(texto)

    engenharia = calcular_rebobinagem(dados, texto)

    return dados, engenharia, texto
