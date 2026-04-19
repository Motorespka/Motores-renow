"""
Area aproximada de condutor cobre nu (mm2) a partir de AWG inteiro.

Uso: alerta conservador **fio x corrente da placa** (nao substitui norma nem desenho de bobina).
Densidade de referencia interna ~2,0 A/mm2 para magnet wire em servico continuo grosseiro.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# Cobre nu, aproximado (mm2) — valores comuns de tabelas de engenharia.
AWG_SOLID_CU_MM2: Dict[int, float] = {
    8: 8.37,
    9: 6.63,
    10: 5.26,
    11: 4.17,
    12: 3.31,
    13: 2.63,
    14: 2.08,
    15: 1.65,
    16: 1.31,
    17: 1.04,
    18: 0.823,
    19: 0.653,
    20: 0.518,
    21: 0.410,
    22: 0.324,
    23: 0.258,
    24: 0.205,
    25: 0.162,
    26: 0.128,
    27: 0.102,
    28: 0.0804,
    29: 0.0646,
    30: 0.0509,
    31: 0.0401,
    32: 0.0320,
    33: 0.0254,
    34: 0.0201,
    35: 0.0159,
    36: 0.0127,
}


def awg_integer_to_mm2(awg: int) -> Optional[float]:
    return AWG_SOLID_CU_MM2.get(int(awg))


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_explicit_mm2_from_raw(raw: Any) -> Optional[float]:
    """Ex.: ``1,25 mm2``, ``0.8mm2``."""
    s = _to_text(raw).lower().replace(",", ".")
    m = re.search(r"(\d+\.?\d*)\s*mm\s*2", s)
    if not m:
        m = re.search(r"(\d+\.?\d*)\s*mm2", s)
    if not m:
        return None
    try:
        v = float(m.group(1))
    except ValueError:
        return None
    if 0.03 <= v <= 50.0:
        return v
    return None


def infer_awg_from_gauge_token(token: Optional[str], raw: Any) -> Optional[int]:
    """
    Se o texto bruto menciona AWG, usa o numero extraido.
    Senao, inteiro 8..36 no token e tratado como AWG (convencao ``NxAWG`` em fichas).
    """
    raw_s = _to_text(raw)
    if re.search(r"\bawg\b", raw_s, re.I):
        m = re.search(r"awg\s*(\d{1,2})\b", raw_s, re.I)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                return None
    g = _to_text(token)
    if not g.isdigit():
        return None
    n = int(g)
    if 8 <= n <= 36:
        return n
    return None


def conductor_area_mm2_from_principal_fios(
    pr_f: Dict[str, Any],
) -> Tuple[Optional[float], List[str]]:
    """Retorna (mm2 por condutor, notas)."""
    notes: List[str] = []
    raw = pr_f.get("raw")
    mm2 = parse_explicit_mm2_from_raw(raw)
    if mm2 is not None:
        notes.append("Fio: area explicita em mm2 no texto.")
        return mm2, notes
    awg = infer_awg_from_gauge_token(pr_f.get("gauge_token"), raw)
    if awg is None:
        return None, notes
    a = awg_integer_to_mm2(awg)
    if a is None:
        return None, notes
    notes.append(f"Fio: AWG {awg} ~ {a:g} mm2 (cobre nu, referencia).")
    return a, notes


def check_wire_vs_plate_current(
    *,
    pr_f: Dict[str, Any],
    current_line_a: Optional[float],
    density_a_per_mm2: float = 2.0,
) -> Optional[Dict[str, Any]]:
    """
    Se houver corrente de placa e area estimada, compara com densidade conservadora.
    Retorna dict de alerta ou None.
    """
    if current_line_a is None or float(current_line_a) <= 0:
        return None
    area, _notes = conductor_area_mm2_from_principal_fios(pr_f)
    if area is None or area <= 0:
        return None
    par = pr_f.get("parallel")
    try:
        npar = int(par) if par is not None else 1
    except (TypeError, ValueError):
        npar = 1
    npar = max(1, npar)
    i_cond = float(current_line_a) / float(npar)
    s_need = i_cond / float(density_a_per_mm2)
    if area + 1e-9 < s_need * 0.88:
        return {
            "code": "fio_vs_corrente_placa",
            "severity": "alerta",
            "message": (
                f"Secao estimada do fio principal (~{area:g} mm2 por via, {npar} via(s)) parece "
                f"apertada face a corrente de placa (~{float(current_line_a):g} A) usando referencia interna "
                f"~{density_a_per_mm2:g} A/mm2 — conferir bitola real, paralelo e desenho."
            ),
            "heuristic": True,
        }
    return None
