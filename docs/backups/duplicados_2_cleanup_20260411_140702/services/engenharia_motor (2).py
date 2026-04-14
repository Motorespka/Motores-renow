import re


def extrair_numeros(texto):
    return re.findall(r"\d+", texto)


def extrair_passos(texto):
    match = re.search(r"PASSOS.*?([\d\-\s]+)", texto)
    return extrair_numeros(match.group()) if match else []


def extrair_espiras(texto):
    match = re.search(r"ESPIRAS.*?([\d\-\s]+)", texto)
    return extrair_numeros(match.group()) if match else []


def extrair_fio(texto):
    match = re.search(r"\d+\s?X\s?\d+", texto)
    return match.group().replace(" ", "") if match else ""


def identificar_tipo_motor(rpm):
    if not rpm:
        return ""

    if "3500" in rpm or "3600" in rpm:
        return "2 polos"
    if "1750" in rpm or "1800" in rpm:
        return "4 polos"
    if "1150" in rpm or "1200" in rpm:
        return "6 polos"

    return ""


def calcular_rebobinagem(dados, texto):

    espiras = extrair_espiras(texto)

    resultado = {
        "passos": extrair_passos(texto),
        "espiras_originais": espiras,
        "fio_original": extrair_fio(texto),
        "tipo_motor": identificar_tipo_motor(dados.get("rpm"))
    }

    if espiras:
        esp_int = list(map(int, espiras))
        media = sum(esp_int) / len(esp_int)

        resultado["media_espiras"] = round(media)
        resultado["espiras_mais_10"] = round(media * 1.10)
        resultado["espiras_menos_10"] = round(media * 0.90)

    return resultado
