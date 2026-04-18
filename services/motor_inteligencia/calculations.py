"""
Cálculos elétricos e mecânicos base (funções puras).

Quando faltar dado indispensável, os campos derivados ficam ``None`` e
``insufficient_data`` / ``notes`` explicam o motivo — **nunca** inventamos
números silenciosamente.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

RAIZ_3 = math.sqrt(3.0)


def _result(
    value: Optional[float],
    *,
    ok: bool,
    insufficient_data: bool,
    notes: List[str],
    heuristic: bool = False,
) -> Dict[str, Any]:
    return {
        "value": value,
        "ok": ok,
        "insufficient_data": insufficient_data,
        "notes": notes,
        "heuristic": heuristic,
    }


def calc_ns_rpm(frequency_hz: Optional[float], poles: Optional[int]) -> Dict[str, Any]:
    """Rotação síncrona: ``ns = 120 * f / p`` (motor de indução, modelo clássico)."""
    notes: List[str] = []
    if frequency_hz is None or poles is None or poles <= 0:
        return _result(
            None,
            ok=False,
            insufficient_data=True,
            notes=notes + ["Dados insuficientes: frequência e/ou polos ausentes ou inválidos."],
        )
    if frequency_hz <= 0:
        return _result(None, ok=False, insufficient_data=True, notes=notes + ["Frequência não positiva."])
    ns = 120.0 * float(frequency_hz) / float(poles)
    notes.append("Modelo clássico ns=120f/p; válido para máquinas síncronas de referência em campo AC.")
    return _result(round(ns, 3), ok=True, insufficient_data=False, notes=notes, heuristic=False)


def calc_slip_percent(ns_rpm: Optional[float], rpm_nominal: Optional[float]) -> Dict[str, Any]:
    """Escorregamento percentual: ``((ns - n) / ns) * 100``."""
    notes: List[str] = []
    if ns_rpm is None or rpm_nominal is None:
        return _result(
            None,
            ok=False,
            insufficient_data=True,
            notes=notes + ["Dados insuficientes: ns e/ou RPM nominal ausentes."],
        )
    if ns_rpm <= 0:
        return _result(None, ok=False, insufficient_data=True, notes=notes + ["ns inválido."])
    slip = ((ns_rpm - rpm_nominal) / ns_rpm) * 100.0
    notes.append(
        "Escorregamento calculado a partir de RPM nominal informado; "
        "motor síncrono ou leitura errada pode distorcer o valor."
    )
    return _result(round(slip, 4), ok=True, insufficient_data=False, notes=notes, heuristic=True)


def calc_pin_kw(
    *,
    tension_v: Optional[float],
    current_a: Optional[float],
    power_factor: Optional[float],
    phases: str,
) -> Dict[str, Any]:
    """
    Potência elétrica de entrada estimada (kW).

    Trifásico (heurística): ``sqrt(3) * V * I * fp / 1000`` com V como tensão de linha.
    Monofásico (heurística): ``V * I * fp / 1000`` (circuito simplificado; ligação exata não inferida).
    """
    notes: List[str] = []
    if tension_v is None or current_a is None or power_factor is None:
        return _result(
            None,
            ok=False,
            insufficient_data=True,
            notes=notes + ["Dados insuficientes: tensão, corrente e/ou fator de potência ausentes."],
        )
    if phases == "unknown":
        return _result(
            None,
            ok=False,
            insufficient_data=True,
            notes=notes
            + [
                "Dados insuficientes: fases mono/tri não identificadas — não calcular Pin sem assumir ligação."
            ],
        )
    if phases == "tri":
        pin = RAIZ_3 * tension_v * current_a * power_factor / 1000.0
        notes.append(
            "Heurística Pin trifásico: tensão tratada como linha-linha; confirmação depende de esquema Y/D."
        )
    else:
        pin = tension_v * current_a * power_factor / 1000.0
        notes.append(
            "Heurística Pin monofásico: modelo unifilar simplificado; capacitor/auxiliar não modelados nesta v1."
        )
    return _result(round(pin, 6), ok=True, insufficient_data=False, notes=notes, heuristic=True)


def calc_pout_kw(pin_kw: Optional[float], efficiency: Optional[float]) -> Dict[str, Any]:
    """Potência de saída mecânica aproximada: ``Pout = Pin * rendimento``."""
    notes: List[str] = []
    if pin_kw is None or efficiency is None:
        return _result(
            None,
            ok=False,
            insufficient_data=True,
            notes=notes + ["Dados insuficientes: Pin e/ou rendimento ausentes."],
        )
    if not (0.0 < efficiency <= 1.0):
        return _result(None, ok=False, insufficient_data=True, notes=notes + ["Rendimento fora do intervalo (0,1]."])
    pout = pin_kw * efficiency
    notes.append("Pout derivado de Pin e rendimento; ignora perdas mecânicas ventilação/atrito fora do rendimento elétrico.")
    return _result(round(pout, 6), ok=True, insufficient_data=False, notes=notes, heuristic=True)


def calc_torque_nm(pout_kw: Optional[float], rpm_nominal: Optional[float]) -> Dict[str, Any]:
    """Torque nominal aproximado: ``T = 9550 * Pout[kW] / n[rpm]``."""
    notes: List[str] = []
    if pout_kw is None or rpm_nominal is None or rpm_nominal <= 0:
        return _result(
            None,
            ok=False,
            insufficient_data=True,
            notes=notes + ["Dados insuficientes: Pout e/ou RPM ausentes ou RPM não positivo."],
        )
    tq = 9550.0 * pout_kw / rpm_nominal
    notes.append("Torque a partir de Pout e RPM; valor nominal de catálogo pode diferir por serviço/fator.")
    return _result(round(tq, 4), ok=True, insufficient_data=False, notes=notes, heuristic=True)


def estimate_slip_from_nameplate(
    ns_rpm: Optional[float], rpm_nominal: Optional[float]
) -> Optional[Dict[str, Any]]:
    """
    Estimativa explícita de escorregamento quando há ns e RPM (sem inventar outros campos).
    """
    if ns_rpm is None or rpm_nominal is None or ns_rpm <= 0:
        return None
    slip = ((ns_rpm - rpm_nominal) / ns_rpm) * 100.0
    return {
        "field": "slip_percent",
        "value": round(slip, 4),
        "estimado": True,
        "origem": "RPM nominal + ns calculado a partir de f e polos",
        "confianca": 0.65 if rpm_nominal < ns_rpm else 0.25,
        "heuristic": True,
        "notes": ["Se RPM >= ns, escorregamento não é fisicamente válido para indução clássica — revisar dados."],
    }


def compute_derived_metrics(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agrega todos os derivados num único dicionário (valores simples + metadados por cálculo).
    """
    f_hz = normalized.get("frequency_hz")
    poles = normalized.get("poles")
    rpm = normalized.get("rpm_nominal")
    v = normalized.get("tension_v_primary")
    i = normalized.get("current_a")
    fp = normalized.get("power_factor")
    eta = normalized.get("efficiency")
    phases = normalized.get("phases") or "unknown"

    ns_block = calc_ns_rpm(f_hz if isinstance(f_hz, (int, float)) else None, poles)
    ns_val = ns_block["value"]

    slip_block = calc_slip_percent(ns_val, rpm if isinstance(rpm, (int, float)) else None)
    pin_block = calc_pin_kw(tension_v=v, current_a=i, power_factor=fp, phases=phases)
    pout_block = calc_pout_kw(pin_block.get("value"), eta if isinstance(eta, (int, float)) else None)
    torque_block = calc_torque_nm(pout_block.get("value"), rpm if isinstance(rpm, (int, float)) else None)

    calculos_concluidos: List[str] = []
    calculos_impossiveis: List[Dict[str, str]] = []

    for name, blk in (
        ("ns_rpm", ns_block),
        ("slip_percent", slip_block),
        ("pin_kw", pin_block),
        ("pout_kw", pout_block),
        ("torque_nm", torque_block),
    ):
        if blk.get("insufficient_data"):
            calculos_impossiveis.append(
                {"calculo": name, "motivo": "; ".join(blk.get("notes") or ["dados insuficientes"])}
            )
        elif blk.get("value") is not None:
            calculos_concluidos.append(name)

    estimates: List[Dict[str, Any]] = []
    est = estimate_slip_from_nameplate(ns_val, rpm if isinstance(rpm, (int, float)) else None)
    if est:
        estimates.append(est)

    return {
        "ns_rpm": ns_block,
        "slip_percent": slip_block,
        "pin_kw": pin_block,
        "pout_kw": pout_block,
        "torque_nm": torque_block,
        "calculos_concluidos": calculos_concluidos,
        "calculos_impossiveis": calculos_impossiveis,
        "estimates": estimates,
    }
