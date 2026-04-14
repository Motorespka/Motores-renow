import json
import os

ARQ = "db/base_oficina.json"


def iniciar():

    os.makedirs("db", exist_ok=True)

    if not os.path.exists(ARQ):
        with open(ARQ,"w") as f:
            json.dump([],f)


def registrar_base(dados, engenharia):

    iniciar()

    with open(ARQ,"r") as f:
        banco = json.load(f)

    banco.append({
        "rpm": dados.get("rpm"),
        "tensao": dados.get("tensao"),
        "espiras": engenharia.get("espiras_originais"),
        "fio": engenharia.get("fio_original")
    })

    with open(ARQ,"w") as f:
        json.dump(banco,f,indent=2)


def prever_motor(dados):

    iniciar()

    with open(ARQ,"r") as f:
        banco = json.load(f)

    similares = [
        m for m in banco
        if m["rpm"] == dados.get("rpm")
        and m["tensao"] == dados.get("tensao")
    ]

    if not similares:
        return None

    espiras = [int(m["espiras"]) for m in similares if m["espiras"]]

    if not espiras:
        return None

    media = int(sum(espiras)/len(espiras))

    return {
        "amostras": len(espiras),
        "espiras_previstas": media
    }
