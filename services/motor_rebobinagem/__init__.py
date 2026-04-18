"""
Inteligência de rebobinagem / oficina (Moto-Renow) — read-only, modular, evolutiva.

Não persiste dados nem altera fluxos existentes. Heurísticas são explícitas nas notas
e na saída de validação.
"""

from __future__ import annotations

from typing import Any, Dict

from services.motor_rebobinagem.analysis import analyze_rewinding_coherence
from services.motor_rebobinagem.normalization import normalize_rewinding_input
from services.motor_rebobinagem.serialization import prepare_fastapi_rebobinagem_payload
from services.motor_rebobinagem.signature import build_rewinding_signature, prepare_similarity_query

__all__ = [
    "analyze_rewinding_coherence",
    "normalize_rewinding_input",
    "build_rewinding_signature",
    "prepare_similarity_query",
    "prepare_fastapi_rebobinagem_payload",
    "REBOBINAGEM_SEVERITY_COLORS",
    "rebobinagem_status_color",
]


REBOBINAGEM_SEVERITY_COLORS: Dict[str, str] = {
    "ok": "#16a34a",
    "alerta": "#ca8a04",
    "critico": "#dc2626",
    "insuficiente": "#64748b",
}


def rebobinagem_status_color(status: str) -> str:
    s = (status or "").strip().lower()
    return REBOBINAGEM_SEVERITY_COLORS.get(s, REBOBINAGEM_SEVERITY_COLORS["insuficiente"])
