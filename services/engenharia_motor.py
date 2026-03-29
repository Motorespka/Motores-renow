import re

# ==========================
# LIMPEZA NUMÉRICA
# ==========================
def numeros(texto):
    return re.findall(r"\d+", texto)


# ==========================
# IDENTIFICAR ESPIRAS
# ==========================
def extrair_espiras(texto):

    padrao = r"ESPIRAS\s*([\d\s\-]+)"
    match = re.search(padrao, texto)

    if match:
        return numeros(match.group())

    return []


# ==========================
# IDENTIFICAR PASSOS
# ==========================
def extrair_passos(texto):

    padrao = r"PASSOS.*?([\d\s\-]+)"
    match = re.search(padrao, texto)

    if match:
        return numeros(match.group())

    return []


# ==========================
# IDENTIFICAR FIO
# ==========================
def extrair_fio(texto):

    fio = re.search(r"\d+\s?X\s?\d+", texto)

    if fio:
        return fio.group()

    return ""


# ==========================
# CALCULO ENGENHEIRO
# ==========================
def calcular_rebobinagem(dados, texto):

    resultado = {}

    passos = extrair_passos(texto)
    espiras = extrair_espiras(texto)
    fio = extrair_fio(texto)

    resultado["passos"] = passos
    resultado["espiras"] = espiras
    resultado["fio"] = fio

    # =====================
    # INTELIGÊNCIA REAL
    # =====================

    if espiras:
        media = sum(map(int, espiras)) / len(espiras)
        resultado["media_espiras"] = round(media)

        # regra prática rebobinador
        resultado["espiras_recomendadas"] = round(media * 1.10)

    if dados.get("rpm"):
        if "3500" in dados["rpm"]:
            resultado["tipo_motor"] = "2 polos"
        elif "1750" in dados["rpm"]:
            resultado["tipo_motor"] = "4 polos"

    return resultado
