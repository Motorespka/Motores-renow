import easyocr
import numpy as np
import cv2
import re

from services.engenharia_motor import calcular_rebobinagem

reader = easyocr.Reader(['pt','en'], gpu=False)


def preprocessar(file):

    bytes_data = np.asarray(bytearray(file.read()), dtype=np.uint8)
    img = cv2.imdecode(bytes_data, 1)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    return gray


def ler_texto(file):

    img = preprocessar(file)
    resultado = reader.readtext(img, detail=0)

    return " ".join(resultado).upper()


def extrair_dados(texto):

    dados = {}

    if "WEG" in texto:
        dados["marca"] = "WEG"

    rpm = re.search(r"\d{4}\s?RPM", texto)
    if rpm:
        dados["rpm"] = rpm.group()

    tensao = re.search(r"\d{2,3}\/\d{2,3}", texto)
    if tensao:
        dados["tensao"] = tensao.group()

    corrente = re.search(r"\d+[.,]\d+\s?A", texto)
    if corrente:
        dados["corrente"] = corrente.group()

    return dados


def ler_placa_motor(file):

    texto = ler_texto(file)
    dados = extrair_dados(texto)
    engenharia = calcular_rebobinagem(dados, texto)

    return dados, engenharia, texto
