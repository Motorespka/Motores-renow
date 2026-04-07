from __future__ import annotations

from typing import Dict, List


def _parse_tensoes(tensao_v: str) -> List[str]:
    if not tensao_v:
        return []

    raw = str(tensao_v).replace("V", "").replace("v", "")
    tokens = raw.replace("/", ",").replace(";", ",").split(",")

    vals: List[str] = []
    for token in tokens:
        t = token.strip()
        if not t:
            continue
        if t.isdigit():
            vals.append(t)

    uniq: List[str] = []
    seen = set()
    for val in vals:
        if val not in seen:
            uniq.append(val)
            seen.add(val)

    return sorted(uniq, key=int)


def _detectar_fases(raw) -> int | None:
    if raw is None:
        return None

    txt = str(raw).strip().lower()
    if not txt:
        return None

    if "mono" in txt:
        return 1
    if "tri" in txt:
        return 3

    try:
        return int(float(txt.replace(",", ".")))
    except Exception:
        return None


def obter_configuracoes_ligacao(motor_data: Dict) -> str:
    fases = _detectar_fases(motor_data.get("fases"))
    tensoes = _parse_tensoes(motor_data.get("tensao_v", ""))
    origem_tensao = str(motor_data.get("tensao_v", "")).strip() or "nao informada"

    configs: List[str] = []

    if fases == 1:
        if not tensoes:
            return f"Motor monofasico. Tensao {origem_tensao}. Consultar placa do fabricante."

        if len(tensoes) == 1:
            return f"Tensao unica {tensoes[0]}V. Fechamento conforme placa do fabricante."

        configs.append(f"Para {tensoes[0]}V: fechamento de baixa tensao (tipicamente paralelo).")
        configs.append(f"Para {tensoes[1]}V: fechamento de alta tensao (tipicamente serie).")
        if len(tensoes) > 2:
            configs.append(f"Tensoes adicionais: {', '.join(tensoes[2:])}. Verificar diagrama especifico.")
        return "\n".join(configs)

    if fases == 3:
        if not tensoes:
            return f"Motor trifasico. Tensao {origem_tensao}. Consultar placa do fabricante."

        tens_set = set(tensoes)
        if {"220", "380"}.issubset(tens_set):
            configs.append("220V: Triangulo (Delta).")
            configs.append("380V: Estrela (Y).")
        if {"380", "660"}.issubset(tens_set):
            configs.append("380V: Triangulo (Delta).")
            configs.append("660V: Estrela (Y).")

        if not configs and len(tensoes) == 1:
            t = tensoes[0]
            if t == "220":
                configs.append("220V: tipicamente Triangulo (Delta).")
            elif t in {"380", "440", "660"}:
                configs.append(f"{t}V: tipicamente Estrela (Y).")
            else:
                configs.append(f"{t}V: consultar diagrama da placa.")

        extras = [t for t in tensoes if t not in {"220", "380", "440", "660"}]
        if extras:
            configs.append(f"Outras tensoes: {', '.join(extras)}. Verificar diagrama especifico.")

        return "\n".join(configs) if configs else "Consultar placa para configuracao de ligacao."

    return f"Tipo de motor nao especificado (fases={motor_data.get('fases')}). Consulte o manual."
