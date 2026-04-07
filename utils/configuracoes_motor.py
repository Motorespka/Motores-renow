from __future__ import annotations

from typing import Dict, List


def _parse_tensoes(tensao_v: str) -> List[str]:
    if not tensao_v:
        return []
    raw = str(tensao_v).replace("V", "").replace("v", "")
    tokens = raw.replace("/", ",").replace(";", ",").split(",")
    vals = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if t.isdigit():
            vals.append(t)
    # remove duplicados preservando ordem
    unique = []
    seen = set()
    for v in vals:
        if v not in seen:
            unique.append(v)
            seen.add(v)
    return sorted(unique, key=int)


def _detectar_fases(raw) -> int | None:
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if not s:
        return None
    if "mono" in s:
        return 1
    if "tri" in s:
        return 3
    try:
        return int(float(s.replace(",", ".")))
    except Exception:
        return None


def obter_configuracoes_ligacao(motor_data: Dict) -> str:
    """
    Retorna orientacao textual de ligacao de cabos (base tecnica geral).
    """
    fases = _detectar_fases(motor_data.get("fases"))
    tensoes = _parse_tensoes(motor_data.get("tensao_v", ""))
    origem = str(motor_data.get("tensao_v", "")).strip() or "nao informada"

    configs: List[str] = []

    # Monofasico
    if fases == 1:
        if not tensoes:
            configs.append(f"Motor monofasico. Tensao {origem}. Consulte o diagrama de placa.")
        elif len(tensoes) == 1:
            configs.append(f"Tensao unica {tensoes[0]}V. Fechamento conforme placa do fabricante.")
        else:
            configs.append(f"Para {tensoes[0]}V: fechamento de baixa tensao (tipicamente paralelo).")
            configs.append(f"Para {tensoes[1]}V: fechamento de alta tensao (tipicamente serie).")
            if len(tensoes) > 2:
                configs.append(f"Tensoes adicionais: {', '.join(tensoes[2:])}. Consultar diagrama especifico.")
        return "\n".join(configs)

    # Trifasico
    if fases == 3:
        if not tensoes:
            configs.append(f"Motor trifasico. Tensao {origem}. Consulte o manual do fabricante.")
            return "\n".join(configs)

        tensoes_set = set(tensoes)
        if {"220", "380"}.issubset(tensoes_set):
            configs.append("Para 220V: ligacao em Triangulo (Delta).")
            configs.append("Para 380V: ligacao em Estrela (Y).")
        if {"380", "660"}.issubset(tensoes_set):
            configs.append("Para 380V: ligacao em Triangulo (Delta).")
            configs.append("Para 660V: ligacao em Estrela (Y).")
        if {"220", "380", "440"}.issubset(tensoes_set):
            configs.append("Para 440V: verificar diagrama especifico do fabricante.")

        if not configs and len(tensoes) == 1:
            t = tensoes[0]
            if t in {"220"}:
                configs.append("Tensao unica 220V: tipicamente Triangulo (Delta).")
            elif t in {"380", "440", "660"}:
                configs.append(f"Tensao unica {t}V: tipicamente Estrela (Y).")
            else:
                configs.append(f"Tensao unica {t}V: consultar diagrama de placa.")
        elif len(tensoes) > 0:
            mapeadas = {"220", "380", "440", "660"}
            extras = [t for t in tensoes if t not in mapeadas]
            if extras:
                configs.append(f"Outras tensoes suportadas: {', '.join(extras)}. Consultar diagrama especifico.")

        return "\n".join(configs)

    # Desconhecido
    return f"Tipo de motor nao especificado (fases={motor_data.get('fases')}). Consulte o manual."
