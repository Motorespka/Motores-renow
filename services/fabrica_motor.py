import math

DENSIDADE_CORRENTE = 4.5
RENDIMENTO = 0.85
FP = 0.82


def estimar_potencia(corrente, tensao):
    try:
        corrente = float(corrente.replace(",", "."))
        tensao = float(tensao)

        kw = (math.sqrt(3) * tensao * corrente * FP * RENDIMENTO) / 1000
        return round(kw, 2)
    except:
        return None


def calcular_bitola(corrente):
    try:
        corrente = float(corrente.replace(",", "."))
        area = corrente / DENSIDADE_CORRENTE
        diametro = math.sqrt((4 * area) / math.pi)

        return {
            "area": round(area, 2),
            "diametro": round(diametro, 2)
        }
    except:
        return None


def analise_fabrica(dados):

    tensao = dados.get("tensao", "")
    corrente = dados.get("corrente", "")

    if "/" in tensao:
        tensao = tensao.split("/")[0]

    return {
        "potencia_kw": estimar_potencia(corrente, tensao),
        "bitola": calcular_bitola(corrente),
    }
