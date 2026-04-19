"""
Textos de preenchimento para UI quando a ficha está lacunar (read-only).

Não grava na base: só orienta o operador (ex.: RPM síncrono teórico quando falta RPM da placa).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from utils.motor_view import is_empty


def _as_joined_text(value: Any) -> str:
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
        return ", ".join(items) if items else ""
    if value is None:
        return ""
    return str(value).strip()


def parse_poles_count(value: Any) -> Optional[int]:
    raw = _as_joined_text(value).upper().replace("POLOS", "P").replace(" ", "")
    if not raw:
        return None
    m = re.search(r"(\d+)\s*P\b", raw)
    if not m:
        m = re.search(r"^(\d+)$", raw)
    if not m:
        m = re.search(r"(\d+)", raw)
    if not m:
        return None
    p = int(m.group(1))
    if p % 2 == 0 and 2 <= p <= 24:
        return p
    return None


def parse_frequency_hz(value: Any) -> Optional[float]:
    raw = _as_joined_text(value).lower().replace("hz", "").strip()
    if not raw:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)", raw.replace(",", "."))
    if not m:
        return None
    v = float(m.group(1).replace(",", "."))
    if 45.0 <= v <= 65.0:
        return v
    return None


def merge_polos_frequency_hz(
    m: Dict[str, Any],
    motor_info: Dict[str, Any],
) -> Tuple[Optional[int], Optional[float]]:
    poles_raw = None
    for src in (m.get("polos"), motor_info.get("polos")):
        if not is_empty(src):
            poles_raw = src
            break
    freq_raw = None
    for src in (m.get("frequencia_hz"), motor_info.get("frequencia")):
        if not is_empty(src):
            freq_raw = src
            break
    return parse_poles_count(poles_raw), parse_frequency_hz(freq_raw)


def synchronous_rpm_theoretical(f_hz: float, poles: int) -> float:
    return 120.0 * float(f_hz) / float(poles)


def rpm_identificacao_display(m: Dict[str, Any], motor_info: Dict[str, Any]) -> str:
    rpm = m.get("rpm_nominal")
    if not is_empty(rpm):
        return _as_joined_text(rpm)
    p, fhz = merge_polos_frequency_hz(m, motor_info)
    if p is not None and fhz is not None:
        ns = synchronous_rpm_theoretical(fhz, p)
        nsi = int(round(ns))
        return f"≈ {nsi} rpm (síncrono {fhz:g} Hz · {p}p; RPM placa não consta)"
    return "— (RPM placa: informe polos + Hz)"


def potencia_identificacao_display(m: Dict[str, Any], motor_info: Dict[str, Any]) -> str:
    for src in (m.get("potencia_hp_cv"), motor_info.get("potencia")):
        if not is_empty(src):
            return _as_joined_text(src)
    return "— (CV/kW não consta)"


def tensao_identificacao_display(m: Dict[str, Any], motor_info: Dict[str, Any]) -> str:
    for src in (m.get("tensao_v"), motor_info.get("tensao")):
        t = _as_joined_text(src)
        if t and not is_empty(t):
            return t
    return "— (tensão não consta)"


def corrente_identificacao_display(m: Dict[str, Any], motor_info: Dict[str, Any]) -> str:
    for src in (m.get("corrente_nominal_a"), motor_info.get("corrente")):
        t = _as_joined_text(src)
        if t and not is_empty(t):
            return t
    return "— (corrente não consta)"


def campo_ou_nao_consta(value: Any, *, empty_msg: str = "—") -> str:
    t = _as_joined_text(value)
    if t and not is_empty(t):
        return t
    return empty_msg
