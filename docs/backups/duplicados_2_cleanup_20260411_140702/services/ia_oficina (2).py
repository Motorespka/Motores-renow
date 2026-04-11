import json
import os
from datetime import datetime

ARQUIVO = "db/historico_motores.json"


# ==============================
# GARANTE BANCO
# ==============================

def iniciar_banco():

    os.makedirs("db", exist_ok=True)

    if not os.path.exists(ARQUIVO):
        with open(ARQUIVO, "w") as f:
            json.dump([], f)


# ==============================
# SALVAR EXPERIÊNCIA REAL
# ==============================

def registrar_rebobinagem(dados, engenharia, resultado):

    iniciar_banco()

    registro = {
        "data": str(datetime.now()),
        "marca": dados.get("marca"),
        "rpm": dados.get("rpm"),
        "tensao": dados.get("tensao"),
        "corrente": dados.get("corrente"),
        "espiras": engenharia.get("espiras_originais"),
        "fio": engenharia.get("fio_original"),
        "resultado": resultado
    }

    with open(ARQUIVO, "r") as f:
        banco = json.load(f)

    banco.append(registro)

    with open(ARQUIVO, "w") as f:
        json.dump(banco, f, indent=2)


# ==============================
# IA APRENDE PADRÕES
# ==============================

def inteligencia_oficina(dados):

    iniciar_banco()

    with open(ARQUIVO, "r") as f:
        banco = json.load(f)

    semelhantes = [
        m for m in banco
        if m["rpm"] == dados.get("rpm")
        and m["tensao"] == dados.get("tensao")
    ]

    if not semelhantes:
        return None

    espiras = [
        m["espiras"]
        for m in semelhantes
        if m["resultado"] == "OK"
    ]

    if not espiras:
        return None

    media = int(sum(espiras) / len(espiras))

    return {
        "quantidade": len(espiras),
        "espiras_recomendadas": media
    }
