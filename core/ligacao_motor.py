def _split_values(value):
    """Divide strings como '220/380' ou '220, 380' em lista limpa."""
    if value is None:
        return []
    raw = str(value).replace("V", "").replace("v", "")
    tokens = raw.replace("/", ",").replace(";", ",").split(",")
    return [t.strip() for t in tokens if t and t.strip()]


def _to_int(value):
    try:
        return int(float(str(value).replace(",", ".").strip()))
    except Exception:
        return None


def _sorted_tensoes(values):
    unique = []
    seen = set()
    for v in values:
        if v not in seen:
            unique.append(v)
            seen.add(v)
    return sorted(unique, key=lambda x: _to_int(x) if _to_int(x) is not None else 999999)


def _corrente_for(correntes, idx):
    if idx < len(correntes):
        return correntes[idx]
    return "-"


def _is_monofasico(motor):
    fases = str(motor.get("fases", "")).strip().lower()
    tipo = str(motor.get("tipo_enrolamento", "")).strip().lower()
    if "mono" in fases or fases == "1":
        return True
    if "mono" in tipo:
        return True
    return False


def gerar_ligacoes_motor(motor):
    """
    Gera recomendacoes de fechamento por tensao baseada em pratica industrial.
    """
    tensoes = _sorted_tensoes(_split_values(motor.get("tensao_v")))
    correntes = _split_values(motor.get("corrente_nominal_a"))
    ligacoes = []

    # 1) Monofasico
    if _is_monofasico(motor):
        if not tensoes:
            ligacoes.append(
                {
                    "titulo": "Monofasico",
                    "descricao": "Consultar diagrama de placa para serie/paralelo.",
                    "corrente": _corrente_for(correntes, 0),
                }
            )
            return ligacoes

        if len(tensoes) == 1:
            ligacoes.append(
                {
                    "titulo": f"Monofasico {tensoes[0]}V",
                    "descricao": "Fechamento conforme placa do fabricante.",
                    "corrente": _corrente_for(correntes, 0),
                }
            )
            return ligacoes

        for i, tensao in enumerate(tensoes):
            if i == 0:
                desc = "Tensao baixa: enrolamentos em paralelo (consultar placa)."
            elif i == 1:
                desc = "Tensao alta: enrolamentos em serie (consultar placa)."
            else:
                desc = "Tensao adicional: consultar diagrama especifico."
            ligacoes.append(
                {
                    "titulo": f"Monofasico {tensao}V",
                    "descricao": desc,
                    "corrente": _corrente_for(correntes, i),
                }
            )
        return ligacoes

    # 2) Trifasico
    if not tensoes:
        ligacoes.append(
            {
                "titulo": "Trifasico",
                "descricao": "Sem tensao informada. Consultar placa do motor.",
                "corrente": _corrente_for(correntes, 0),
            }
        )
        return ligacoes

    if len(tensoes) == 1:
        ligacoes.append(
            {
                "titulo": f"Trifasico {tensoes[0]}V",
                "descricao": "Fechamento fixo conforme placa (estrela ou triangulo).",
                "corrente": _corrente_for(correntes, 0),
            }
        )
        return ligacoes

    if len(tensoes) == 2:
        ligacoes.append(
            {
                "titulo": f"{tensoes[0]}V (Baixa)",
                "descricao": "Fechamento em Triangulo (Delta).",
                "corrente": _corrente_for(correntes, 0),
            }
        )
        ligacoes.append(
            {
                "titulo": f"{tensoes[1]}V (Alta)",
                "descricao": "Fechamento em Estrela (Y).",
                "corrente": _corrente_for(correntes, 1),
            }
        )
        return ligacoes

    # 3) Tres ou mais tensoes (ex.: 220/380/440)
    for i, tensao in enumerate(tensoes):
        if i == 0:
            desc = "Triangulo paralelo (baixa tensao)."
        elif i == 1:
            desc = "Estrela paralelo ou triangulo serie."
        elif i == 2:
            desc = "Estrela serie (alta tensao)."
        else:
            desc = "Tensao adicional: consultar diagrama especifico."

        ligacoes.append(
            {
                "titulo": f"{tensao}V",
                "descricao": desc,
                "corrente": _corrente_for(correntes, i),
            }
        )

    return ligacoes
