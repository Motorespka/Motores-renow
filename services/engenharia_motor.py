import re


# ==========================
# UTIL
# ==========================
def extrair_numeros(texto):
    return re.findall(r"\d+", texto)


# ==========================
# PASSOS
# ==========================
def extrair_passos(texto):
    match = re.search(r"PASSOS.*?([\d\-\s]+)", texto)
    if match:
        return extrair_numeros(match.group())
    return []


# ==========================
# ESPIRAS
# ==========================
def extrair_espiras(texto):
    match = re.search(r"ESPIRAS.*?([\d\-\s]+)", texto)
    if match:
        return extrair_numeros(match.group())
    return []


# ==========================
# FIO
# ==========================
def extrair_fio(texto):
    match = re.search(r"\d+\s?X\s?\d+", texto)
    if match:
        return match.group().replace(" ", "")
    return ""


# ==========================
# IDENTIFICA TIPO MOTOR
# ==========================
def identificar_tipo_motor(rpm_texto):

    if not rpm_texto:
        return ""

    if "3500" in rpm_texto or "3600" in rpm_texto:
        return "2 polos"
    if "1750" in rpm_texto or "1800" in rpm_texto:
        return "4 polos"
    if "1150" in rpm_texto or "1200" in rpm_texto:
        return "6 polos"

    return ""


# ==========================
# CALCULO PRINCIPAL
# ==========================
def calcular_rebobinagem(dados, texto):

    resultado = {}

    passos = extrair_passos(texto)
    espiras = extrair_espiras(texto)
    fio = extrair_fio(texto)

    resultado["passos"] = passos
    resultado["espiras_originais"] = espiras
    resultado["fio_original"] = fio

    # média espiras
    if espiras:
        esp_int = list(map(int, espiras))
        media = sum(esp_int) / len(esp_int)

        resultado["media_espiras"] = round(media)
        resultado["espiras_mais_10"] = round(media * 1.10)
        resultado["espiras_menos_10"] = round(media * 0.90)

    # tipo motor
    resultado["tipo_motor"] = identificar_tipo_motor(dados.get("rpm", ""))

    return resultado
