# core/ligacoes_motor.py

def _split(valor):
    if not valor:
        return []
    return [
        v.strip()
        for v in str(valor).replace("/", ",").split(",")
        if v.strip()
    ]


def gerar_ligacoes_motor(motor):

    tipo = str(motor.get("tipo_enrolamento", "")).lower()
    tensoes = _split(motor.get("tensao_v"))
    correntes = _split(motor.get("corrente_nominal_a"))

    qtd = max(len(tensoes), len(correntes))

    ligacoes = []

    # ==================================================
    # MONOFÁSICO
    # ==================================================
    if "mono" in tipo:

        if qtd <= 1:
            ligacoes.append({
                "titulo": "Monofásico 5 Cabos",
                "descricao": "1-2 Principal | 3-4 Auxiliar | 5 Comum"
            })

        else:
            for i in range(qtd):
                tensao = tensoes[i] if i < len(tensoes) else "-"
                corrente = correntes[i] if i < len(correntes) else "-"

                ligacoes.append({
                    "titulo": f"Monofásico 6 Cabos — {tensao}V",
                    "descricao": "(1+3+5) / (2+4+6)",
                    "corrente": corrente
                })

        return ligacoes

    # ==================================================
    # TRIFÁSICO
    # ==================================================
    if qtd == 1:

        ligacoes.append({
            "titulo": "Trifásico 6 Cabos",
            "descricao": "Ligação fixa Estrela ou Triângulo"
        })

    elif qtd == 2:

        ligacoes.append({
            "titulo": f"{tensoes[0]}V",
            "descricao": "Triângulo (Baixa tensão)"
        })

        ligacoes.append({
            "titulo": f"{tensoes[1]}V",
            "descricao": "Estrela (Alta tensão)"
        })

    elif qtd >= 3:

        ligacoes.append({
            "titulo": f"{tensoes[0]}V",
            "descricao": "Paralelo"
        })

        ligacoes.append({
            "titulo": f"{tensoes[1]}V",
            "descricao": "Série"
        })

        ligacoes.append({
            "titulo": f"{tensoes[2]}V",
            "descricao": "Alta tensão"
        })

    return ligacoes
