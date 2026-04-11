
from difflib import SequenceMatcher
import re
from core.aprendizado import sugestao


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def normalizar(texto):
    texto = texto.lower()
    mapa = {
        "cv": "cv",
        "hp": "cv",
        "rpm": "rpm",
        "mono": "monofasico",
        "tri": "trifasico",
        "herc": "hercules",
        "weg": "weg",
    }
    for k, v in mapa.items():
        texto = texto.replace(k, v)
    return texto


def interpretar(texto):
    texto = normalizar(texto)

    dados = {
        "potencia": None,
        "rpm": None,
        "tensao": None,
        "tipo": None,
        "texto": texto
    }

    p = re.search(r"(\d+(\.\d+)?)\s*cv", texto)
    if p:
        dados["potencia"] = p.group(1)

    r = re.search(r"\d{3,4}", texto)
    if r:
        dados["rpm"] = r.group(0)

    t = re.search(r"(110|127|220|380|440)", texto)
    if t:
        dados["tensao"] = t.group(0)

    if "monofasico" in texto:
        dados["tipo"] = "mono"

    if "trifasico" in texto:
        dados["tipo"] = "tri"

    return dados


def score_motor(motor, dados, busca):
    score = 0

    modelo = str(motor.get("modelo", "")).lower()
    marca = str(motor.get("marca", "")).lower()

    score += similar(busca, modelo)
    score += similar(busca, marca)

    if dados["potencia"]:
        if dados["potencia"] in str(motor.get("potencia_hp_cv", "")):
            score += 2

    if dados["rpm"]:
        if dados["rpm"] in str(motor.get("rpm_nominal", "")):
            score += 2

    if dados["tensao"]:
        if dados["tensao"] in str(motor.get("tensao_v", "")):
            score += 2

    aprendidos = sugestao(busca)
    if modelo in aprendidos:
        score += 3

    return score


def gerar_sugestoes(motores, texto):
    texto = texto.lower()
    sugestoes = set()

    for m in motores:
        modelo = str(m.get("modelo", "")).lower()
        if texto in modelo:
            sugestoes.add(modelo)

    return list(sugestoes)[:5]


def motores_equivalentes(motores, motor_base):
    eq = []
    for m in motores:
        if m["id"] == motor_base["id"]:
            continue

        if (
            m.get("potencia_hp_cv") == motor_base.get("potencia_hp_cv")
            and m.get("rpm_nominal") == motor_base.get("rpm_nominal")
        ):
            eq.append(m)

    return eq[:3]


def engenheiro_busca_v4(motores, texto):
    if not texto:
        return motores, []

    texto = normalizar(texto)
    dados = interpretar(texto)

    ranking = []

    for m in motores:
        s = score_motor(m, dados, texto)
        if s > 1:
            ranking.append((s, m))

    ranking.sort(reverse=True, key=lambda x: x[0])
    resultados = [r[1] for r in ranking]

    sugestoes = gerar_sugestoes(motores, texto)

    return resultados, sugestoes
