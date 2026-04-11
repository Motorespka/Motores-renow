import math


def engenharia_automatica(dados):

    try:
        rpm = float(dados.get("rpm",0))
        tensao = float(dados.get("tensao",0))
        corrente = float(dados.get("corrente",0))
    except:
        return {}

    if rpm == 0:
        return {}

    polos = int(120*60/rpm)

    potencia = (tensao*corrente*1.73)/1000

    area_fio = corrente/4

    diametro = math.sqrt((4*area_fio)/math.pi)

    return {
        "polos": polos,
        "potencia_kw": round(potencia,2),
        "area_fio": round(area_fio,2),
        "diametro": round(diametro,2)
    }
