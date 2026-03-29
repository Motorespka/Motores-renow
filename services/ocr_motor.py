import easyocr
import numpy as np
import cv2
import re

# =============================
# INICIALIZA OCR (uma vez só)
# =============================
reader = easyocr.Reader(['pt', 'en'], gpu=False)


# =============================
# MELHORAMENTO DE IMAGEM
# =============================
def preprocessar_imagem(file):

    bytes_data = np.asarray(bytearray(file.read()), dtype=np.uint8)
    img = cv2.imdecode(bytes_data, 1)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # aumenta contraste
    gray = cv2.equalizeHist(gray)

    # remove ruído
    gray = cv2.GaussianBlur(gray, (3,3), 0)

    # binarização adaptativa
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh


# =============================
# EXTRAÇÃO TEXTO
# =============================
def ler_texto_motor(file):

    img = preprocessar_imagem(file)

    resultado = reader.readtext(img, detail=0)

    texto = " ".join(resultado).upper()

    return texto


# =============================
# INTELIGÊNCIA DE MOTOR
# =============================
def extrair_dados_motor(texto):

    dados = {}

    # MARCA
    if "WEG" in texto:
        dados["marca"] = "WEG"

    # MODELO
    modelo = re.search(r"W\d{2}[A-Z]?", texto)
    if modelo:
        dados["modelo"] = modelo.group()

    # RPM
    rpm = re.findall(r"\d{4}\s?RPM", texto)
    if rpm:
        dados["rpm"] = rpm[0]

    # ISOLAÇÃO
    iso = re.search(r"ISOL.? ?([A-Z])", texto)
    if iso:
        dados["isolacao"] = iso.group(1)

    # REGIME
    reg = re.search(r"REG.? ?S\d", texto)
    if reg:
        dados["regime"] = reg.group()

    # TENSÃO
    tensao = re.findall(r"\d{2,3}\/\d{2,3}", texto)
    if tensao:
        dados["tensao"] = tensao[0]

    # CORRENTE
    amp = re.findall(r"\d+[.,]\d+\s?A", texto)
    if amp:
        dados["corrente"] = amp[0]

    # POLOS
    polos = re.search(r"POLOS?\s?(\d+)", texto)
    if polos:
        dados["polos"] = polos.group(1)

    return dados


# =============================
# FUNÇÃO PRINCIPAL
# =============================
def ler_placa_motor(file):

    texto = ler_texto_motor(file)

    dados = extrair_dados_motor(texto)

    return dados, texto
