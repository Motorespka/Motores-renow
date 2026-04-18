"""
Orquestração da análise de coerência de rebobinagem (read-only).

Reutiliza a base ``motor_inteligencia`` apenas para contexto elétrico normalizado,
sem efeitos colaterais de UI ou persistência.
"""

from __future__ import annotations

from typing import Any, Dict

from services.motor_inteligencia.calculations import compute_derived_metrics
from services.motor_inteligencia.normalization import normalize_motor_inteligencia_input
from services.motor_rebobinagem.future_work import suggest_rewinding_future_work
from services.motor_rebobinagem.normalization import normalize_rewinding_input
from services.motor_rebobinagem.signature import build_rewinding_signature, prepare_similarity_query
from services.motor_rebobinagem.validation import (
    build_rewinding_summary_full,
    build_rewinding_summary_one_liner,
    run_rewinding_validation,
)


def _electric_summary(electric_norm: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "power_kw": electric_norm.get("power_kw"),
        "rpm_nominal": electric_norm.get("rpm_nominal"),
        "poles": electric_norm.get("poles"),
        "frequency_hz": electric_norm.get("frequency_hz"),
        "phases": electric_norm.get("phases"),
        "tensions_v": electric_norm.get("tensions_v"),
        "tipo_motor": electric_norm.get("tipo_motor"),
    }


def analyze_rewinding_coherence(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa coerência de cálculo de oficina / rebobinagem face aos dados do motor.

    ``data``: payload ``dados_tecnicos_json`` ou linha já coerced (com ``motor``, bobinagens, etc.).
    """
    electric_norm = normalize_motor_inteligencia_input(data)
    derived = compute_derived_metrics(electric_norm)
    rew_norm = normalize_rewinding_input(data)

    summary_el = _electric_summary(electric_norm)
    signature = build_rewinding_signature(electric_summary=summary_el, rewinding_normalized=rew_norm)

    validation, _conf = run_rewinding_validation(data, rew_norm, electric_norm)
    summary_one = build_rewinding_summary_one_liner(validation, rew_norm)
    summary = build_rewinding_summary_full(validation, rew_norm)
    future = suggest_rewinding_future_work(rew_norm, validation, signature)

    return {
        "rewinding_normalized": rew_norm,
        "electric_context": {
            "normalized": electric_norm,
            "derived_ns_rpm": (derived.get("ns_rpm") or {}).get("value"),
            "derived_slip_percent": (derived.get("slip_percent") or {}).get("value"),
        },
        "signature": signature,
        "similarity_query": prepare_similarity_query(signature),
        "validation": validation,
        "summary_one_liner": summary_one,
        "summary": summary,
        "future_calculations": future,
    }
