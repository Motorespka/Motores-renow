# core/ligacoes_motor.py

def _split(valor):
    """Divide strings como '220/380' ou '220, 380' em uma lista de strings limpas."""
    if not valor:
        return []
    return [
        v.strip()
        for v in str(valor).replace("/", ",").split(",")
        if v.strip()
    ]


def gerar_ligacoes_motor(motor):
    """
    Analisa os dados do motor e gera os esquemas de fechamento
    baseado na quantidade de tensões e tipo de enrolamento.
    """
    tipo = str(motor.get("tipo_enrolamento", "")).lower()
    tensoes = _split(motor.get("tensao_v"))
    correntes = _split(motor.get("corrente_nominal_a"))

    # Define a quantidade de opções baseada no que houver mais (tensão ou corrente)
    qtd = max(len(tensoes), len(correntes))
    ligacoes = []

    # ==================================================
    # 1. LOGICA PARA MOTORES MONOFÁSICOS
    # ==================================================
    if "mono" in tipo:
        if qtd <= 1:
            # Padrão para motores monofásicos simples
            ligacoes.append({
                "titulo": "Monofásico 5 Cabos",
                "descricao": "1-2 Principal | 3-4 Auxiliar | 5 Comum",
                "corrente": correntes[0] if correntes else "-"
            })
        else:
            # Para motores monofásicos de dupla tensão (ex: 110/220V)
            for i in range(qtd):
                tensao = tensoes[i] if i < len(tensoes) else "-"
                corrente = correntes[i] if i < len(correntes) else "-"
                ligacoes.append({
                    "titulo": f"Monofásico 6 Cabos — {tensao}V",
                    "descricao": "Série/Paralelo: (1+3+5) / (2+4+6)",
                    "corrente": corrente
                })
        return ligacoes

    # ==================================================
    # 2. LOGICA PARA MOTORES TRIFÁSICOS
    # ==================================================
    
    # Caso 1: Tensão Única (ex: apenas 380V)
    if qtd == 1:
        ligacoes.append({
            "titulo": "Trifásico 6 Cabos",
            "descricao": "Ligação fixa (Estrela ou Triângulo conforme placa)",
            "corrente": correntes[0] if correntes else "-"
        })

    # Caso 2: Duas Tensões (ex: 220/380V ou 380/660V)
    elif qtd == 2:
        ligacoes.append({
            "titulo": f"{tensoes[0]}V (Baixa)",
            "descricao": "Fechamento em Triângulo (Δ)",
            "corrente": correntes[0] if correntes else "-"
        })
        ligacoes.append({
            "titulo": f"{tensoes[1]}V (Alta)",
            "descricao": "Fechamento em Estrela (Y)",
            "corrente": correntes[1] if len(correntes) > 1 else "-"
        })

    # Caso 3: Três ou mais Tensões (ex: 220/380/440V)
    elif qtd >= 3:
        ligacoes.append({
            "titulo": f"{tensoes[0]}V",
            "descricao": "Triângulo Paralelo",
            "corrente": tensoes[0] if i < len(tensoes) else "-"
        })
        ligacoes.append({
            "titulo": f"{tensoes[1]}V",
            "descricao": "Estrela Paralelo ou Triângulo Série",
            "corrente": correntes[1] if len(correntes) > 1 else "-"
        })
        ligacoes.append({
            "titulo": f"{tensoes[2]}V",
            "descricao": "Estrela Série (Alta Tensão)",
            "corrente": correntes[2] if len(correntes) > 2 else "-"
        })

    return ligacoes
