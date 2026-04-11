import easyocr
import numpy as np
from PIL import Image

reader = easyocr.Reader(["pt","en"], gpu=False)


def analisar_enrolamento(imagem):

    img = Image.open(imagem)
    img = np.array(img)

    texto = reader.readtext(img, detail=0)

    texto_total = " ".join(texto).lower()

    diagnostico = []

    if "queim" in texto_total:
        diagnostico.append("Bobina queimada detectada")

    if "escuro" in texto_total:
        diagnostico.append("Possível sobreaquecimento")

    if not diagnostico:
        diagnostico.append("Nenhuma falha visual clara")

    return diagnostico
