"""
Equivalencias aproximadas para oficina (fio, secao, espiras x tensao).

Nao substitui norma, projeto de bobina nem ensaio; referencia de bancada.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from services.motor_rebobinagem.wire_gauge import AWG_SOLID_CU_MM2, awg_integer_to_mm2


def _awg_list_sorted() -> List[int]:
    return sorted(AWG_SOLID_CU_MM2.keys())


def area_total_mm2(num_parallel: int, awg: int) -> Optional[float]:
    """Secao total (todas as vias em paralelo), mm2."""
    a = awg_integer_to_mm2(awg)
    if a is None or num_parallel < 1:
        return None
    return float(a) * int(num_parallel)


def equivalent_num_parallel(
    n_old: int,
    awg_old: int,
    awg_new: int,
) -> Optional[Dict[str, Any]]:
    """
    Para manter ~a mesma secao de cobre, quantos fios de awg_new substituem
    n_old fios (em paralelo) de awg_old.
    """
    a_tot = area_total_mm2(n_old, awg_old)
    a_one = awg_integer_to_mm2(awg_new)
    if a_tot is None or a_one is None or a_one <= 0:
        return None
    ratio = a_tot / a_one
    n_ceil = max(1, int(math.ceil(ratio)))
    n_floor = max(1, int(math.floor(ratio)))
    return {
        "area_target_mm2": round(a_tot, 6),
        "area_per_new_conductor_mm2": a_one,
        "ratio": round(ratio, 4),
        "n_parallel_ceil": n_ceil,
        "n_parallel_floor": n_floor,
        "area_ceil_mm2": round(n_ceil * a_one, 6),
        "area_floor_mm2": round(n_floor * a_one, 6),
    }


def turns_for_voltage_ratio(
    n_old: float,
    v_old: float,
    v_new: float,
) -> Optional[float]:
    """Espiras de referencia para alterar tensao de alimentacao (modelo ideal, mesma ligacao)."""
    if v_old <= 0 or v_new <= 0 or n_old <= 0:
        return None
    return n_old * (v_new / v_old)


def suggest_awg_combos_for_area(
    target_mm2: float,
    *,
    max_parallel: int = 6,
) -> List[Dict[str, Any]]:
    """
    Combinações (awg, n em paralelo) cujo produto aproxima target_mm2.
    """
    if target_mm2 <= 0 or max_parallel < 1:
        return []
    out: List[Dict[str, Any]] = []
    for awg in _awg_list_sorted():
        a1 = AWG_SOLID_CU_MM2[awg]
        for n in range(1, max_parallel + 1):
            got = a1 * n
            err = abs(got - target_mm2) / max(target_mm2, 1e-9)
            out.append({"awg": awg, "n_parallel": n, "area_mm2": round(got, 6), "rel_error": round(err, 4)})
    out.sort(key=lambda x: (x["rel_error"], x["n_parallel"], x["awg"]))
    return out[:12]


def series_total_turns(turns_per_group: List[float]) -> float:
    return float(sum(turns_per_group))


def parallel_branch_current_split(i_total: float, num_branches: int) -> Optional[float]:
    if num_branches < 1:
        return None
    return i_total / float(num_branches)
