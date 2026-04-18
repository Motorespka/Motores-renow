"""
Camada técnica read-only de cálculos e validação de motores (Moto-Renow).

- Funções puras, sem I/O nem escrita em base de dados.
- Heurísticas documentadas no código e nas notas de saída (nunca como “verdade absoluta”).
- Extensível para rebobinagem, monofásico/trifásico, capacitor e análises futuras.

API principal:
    ``analyze_motor_technical(raw)`` — normalização + derivados + validação + sugestões.
    ``validate_motor(raw)`` — apenas bloco ``validation`` (útil para integrações leves).
    ``suggest_future_calculations(raw)`` — capacidades futuras a partir do estado atual.
"""

from __future__ import annotations

from typing import Any, Dict

from services.motor_inteligencia.future_work import suggest_future_calculations
from services.motor_inteligencia.validation import (
    build_summary_one_liner,
    build_technical_summary,
    run_validation,
    validate_motor,
)
from services.motor_inteligencia.normalization import normalize_motor_inteligencia_input
from services.motor_inteligencia.calculations import compute_derived_metrics
from services.motor_inteligencia.coercion import coerce_supabase_motor_row

__all__ = [
    "analyze_motor_technical",
    "validate_motor",
    "suggest_future_calculations",
    "build_summary_one_liner",
    "SEVERITY_COLORS",
    "status_to_alert_color",
    "coerce_supabase_motor_row",
]


# Cores para badges (verde / amarelo / vermelho + insuficiente em cinza-azulado)
SEVERITY_COLORS: Dict[str, str] = {
    "ok": "#16a34a",  # verde
    "alerta": "#ca8a04",  # âmbar
    "critico": "#dc2626",  # vermelho
    "insuficiente": "#64748b",  # cinza — dados insuficientes para conclusões fortes
}


def status_to_alert_color(status: str) -> str:
    """Mapeia status de validação para cor de alerta (UI / HTML)."""
    s = (status or "").strip().lower()
    if s == "ok":
        return SEVERITY_COLORS["ok"]
    if s == "alerta":
        return SEVERITY_COLORS["alerta"]
    if s == "critico":
        return SEVERITY_COLORS["critico"]
    return SEVERITY_COLORS["insuficiente"]


def analyze_motor_technical(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Análise técnica completa (read-only).

    ``raw`` pode ser:
    - payload normalizado de oficina (``dados_tecnicos_json``),
    - linha de motor do Supabase com chaves planas,
    - ou mistura (a coerção interna prioriza bloco ``motor`` quando existir).
    """
    normalized = normalize_motor_inteligencia_input(raw)
    derived_blocks = compute_derived_metrics(normalized)
    derived = {
        "ns_rpm": (derived_blocks.get("ns_rpm") or {}).get("value"),
        "slip_percent": (derived_blocks.get("slip_percent") or {}).get("value"),
        "pin_kw": (derived_blocks.get("pin_kw") or {}).get("value"),
        "pout_kw": (derived_blocks.get("pout_kw") or {}).get("value"),
        "torque_nm": (derived_blocks.get("torque_nm") or {}).get("value"),
        "_blocks": {k: derived_blocks[k] for k in ("ns_rpm", "slip_percent", "pin_kw", "pout_kw", "torque_nm")},
        "calculos_concluidos": derived_blocks.get("calculos_concluidos"),
        "calculos_impossiveis": derived_blocks.get("calculos_impossiveis"),
        "estimates": derived_blocks.get("estimates"),
    }
    validation = run_validation(normalized, derived_blocks)
    future_calculations = suggest_future_calculations(normalized, derived_blocks, validation)
    summary = build_technical_summary(normalized, derived_blocks, validation)
    summary_one_liner = build_summary_one_liner(normalized, derived_blocks, validation)

    return {
        "input_normalized": normalized,
        "derived": derived,
        "validation": validation,
        "future_calculations": future_calculations,
        "summary": summary,
        "summary_one_liner": summary_one_liner,
    }
