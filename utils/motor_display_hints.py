"""
Textos de preenchimento para UI quando a ficha está lacunar (read-only).

Não grava na base: só orienta o operador (ex.: RPM síncrono teórico quando falta RPM da placa).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from utils.motor_view import is_empty

RPM_INFERIDO_TOOLTIP = (
    "RPM síncrono teórico (120 · Hz ÷ polos) — placa não consta. "
    "Sob carga, motores de indução costumam girar 3-5% abaixo do síncrono."
)


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


_POLOS_KEYS = ("polos", "Polos", "numero_polos", "n_polos", "poles")
_FREQ_KEYS = ("frequencia_hz", "frequencia", "Frequencia", "hz", "Hz")


def _first_present(*sources: Dict[str, Any], keys: Tuple[str, ...]) -> Any:
    """Varre dicionários (na ordem) e chaves (na ordem) buscando o primeiro valor não vazio."""
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in keys:
            value = source.get(key)
            if not is_empty(value):
                return value
    return None


def merge_polos_frequency_hz(
    m: Dict[str, Any],
    motor_info: Dict[str, Any],
) -> Tuple[Optional[int], Optional[float]]:
    poles_raw = _first_present(m, motor_info, keys=_POLOS_KEYS)
    freq_raw = _first_present(m, motor_info, keys=_FREQ_KEYS)
    return parse_poles_count(poles_raw), parse_frequency_hz(freq_raw)


def synchronous_rpm_theoretical(f_hz: float, poles: int) -> float:
    return 120.0 * float(f_hz) / float(poles)


def _format_inferred_rpm(value: Any) -> str:
    txt = _as_joined_text(value)
    if not txt or is_empty(txt):
        return ""
    if txt.startswith(("≈", "~")):
        return txt
    if "rpm" not in txt.lower():
        txt = f"{txt} rpm"
    return f"≈ {txt}"


def rpm_identificacao_display(m: Dict[str, Any], motor_info: Dict[str, Any]) -> str:
    for src in (m.get("rpm_nominal"), m.get("rpm"), motor_info.get("rpm_nominal"), motor_info.get("rpm")):
        if not is_empty(src):
            return _as_joined_text(src)
    for src in (
        m.get("rpm_calculado"),
        m.get("observacao_rpm"),
        motor_info.get("rpm_calculado"),
        motor_info.get("observacao_rpm"),
    ):
        inferred = _format_inferred_rpm(src)
        if inferred:
            return inferred
    p, fhz = merge_polos_frequency_hz(m, motor_info)
    if p is not None and fhz is not None:
        ns = synchronous_rpm_theoretical(fhz, p)
        nsi = int(round(ns))
        return f"≈ {nsi} rpm (síncrono {fhz:g} Hz · {p}p; RPM placa não consta)"
    return "— (RPM placa: informe polos + Hz)"


def is_rpm_inferred(
    m: Dict[str, Any],
    motor_info: Optional[Dict[str, Any]] = None,
) -> bool:
    """True quando o RPM exibido NÃO vem da placa (`rpm_nominal`/`rpm`).

    Útil para decidir se um marcador visual (`≈`, tooltip, ícone) deve ser
    exibido junto ao valor.
    """
    motor_info = motor_info if isinstance(motor_info, dict) else {}
    for src in (
        m.get("rpm_nominal"),
        m.get("rpm"),
        motor_info.get("rpm_nominal"),
        motor_info.get("rpm"),
    ):
        if not is_empty(src):
            return False
    return True


def rpm_numeric_for_filter(
    m: Dict[str, Any],
    motor_info: Optional[Dict[str, Any]] = None,
) -> Optional[float]:
    """Devolve um número de RPM utilizável em filtros de faixa.

    Ordem de fontes (igual à do display): placa (`rpm_nominal`/`rpm`) →
    calculado/observação (`rpm_calculado`/`observacao_rpm`) → síncrono teórico
    (a partir de polos + Hz). Retorna `None` quando nada está disponível para
    inferir um número (filtro deve então tratar o motor como "indefinido").
    """
    motor_info = motor_info if isinstance(motor_info, dict) else {}
    for src in (
        m.get("rpm_nominal"),
        m.get("rpm"),
        motor_info.get("rpm_nominal"),
        motor_info.get("rpm"),
        m.get("rpm_calculado"),
        m.get("observacao_rpm"),
        motor_info.get("rpm_calculado"),
        motor_info.get("observacao_rpm"),
    ):
        txt = _as_joined_text(src)
        if not txt or is_empty(txt):
            continue
        digits = re.search(r"(\d{2,5})", txt.replace(",", "."))
        if digits:
            try:
                return float(digits.group(1))
            except (TypeError, ValueError):
                pass
    p, fhz = merge_polos_frequency_hz(m, motor_info)
    if p is not None and fhz is not None:
        return synchronous_rpm_theoretical(fhz, p)
    return None


def rpm_compact_display(
    m: Dict[str, Any],
    motor_info: Optional[Dict[str, Any]] = None,
    *,
    empty: str = "—",
) -> str:
    """Versão curta para KPIs estreitos (rodapé do holograma, badges, etc.).

    Regras:
      • Placa presente (rpm_nominal / rpm) → devolve só o número/texto, sem "≈".
      • Calculado / observação inferida → "≈ <nº>".
      • Fallback síncrono (polos+Hz) → "≈ <nº>".
      • Nada disponível → `empty`.
    """
    motor_info = motor_info if isinstance(motor_info, dict) else {}
    for src in (m.get("rpm_nominal"), m.get("rpm"), motor_info.get("rpm_nominal"), motor_info.get("rpm")):
        txt = _as_joined_text(src)
        if txt and not is_empty(txt):
            return txt
    for src in (
        m.get("rpm_calculado"),
        m.get("observacao_rpm"),
        motor_info.get("rpm_calculado"),
        motor_info.get("observacao_rpm"),
    ):
        txt = _as_joined_text(src)
        if not txt or is_empty(txt):
            continue
        digits = re.search(r"(\d{2,5})", txt)
        if digits:
            return f"≈ {digits.group(1)}"
        return _format_inferred_rpm(txt)
    p, fhz = merge_polos_frequency_hz(m, motor_info)
    if p is not None and fhz is not None:
        ns = synchronous_rpm_theoretical(fhz, p)
        return f"≈ {int(round(ns))}"
    return empty


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
