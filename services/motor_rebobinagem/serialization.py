"""Serialização JSON-safe para futuros endpoints read-only."""

from __future__ import annotations

from typing import Any, Dict

from services.motor_inteligencia.serialization import intel_report_to_jsonable


def prepare_fastapi_rebobinagem_payload(report: Dict[str, Any]) -> Dict[str, Any]:
    return intel_report_to_jsonable(report)  # type: ignore[return-value]
