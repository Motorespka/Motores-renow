import json
import os

ARQUIVO_DB = "db_aprendizado.json"


# ==============================
# GARANTIR BANCO
# ==============================
def iniciar_db():

    if not os.path.exists(ARQUIVO_DB):
        with open(ARQUIVO_DB, "w") as f:
            json.dump([], f)


# ==============================
# SALVAR MOTOR
# ==============================
def salvar_motor(dados, engenharia):

    iniciar_db()

    registro = {
        "marca": dados.get("marca"),
        "rpm": dados.get("rpm"),
        "tensao": dados.get("tensao"),
        "corrente": dados.get("corrente"),
        "espiras": engenharia.get("media_espiras"),
        "fio": engenharia.get("fio_original"),
    }

    with open(ARQUIVO_DB, "r") as f:
        banco = json.load(f)

    banco.append(registro)

    with open(ARQUIVO_DB, "w") as f:
        json.dump(banco, f, indent=2)


# ==============================
# APRENDER PADRÕES
# ==============================
def sugestao_inteligente(dados):

    iniciar_db()

    with open(ARQUIVO_DB, "r") as f:
        banco = json.load(f)

    similares = [
        m for m in banco
        if m["rpm"] == dados.get("rpm")
        and m["tensao"] == dados.get("tensao")
    ]

    if not similares:
        return None

    espiras = [m["espiras"] for m in similares if m["espiras"]]

    if not espiras:
        return None

    media = sum(espiras) / len(espiras)

    return {
        "espiras_sugeridas": round(media),
        "baseado_em": len(similares)
    }
