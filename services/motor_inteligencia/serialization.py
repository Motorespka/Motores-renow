"""
Serialização JSON-safe de relatórios da camada ``motor_inteligencia``.

Preparado para futura exposição read-only via FastAPI (sem dependência de framework).
"""

from __future__ import annotations

from typing import Any, Dict, List, Union

Jsonable = Union[None, bool, int, float, str, List[Any], Dict[str, Any]]


def intel_report_to_jsonable(obj: Any) -> Any:
    """
    Converte estruturas aninhadas em tipos aceites por ``json.dumps`` padrão.

    Objetos não serializáveis viram ``str(obj)`` (último recurso).
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): intel_report_to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [intel_report_to_jsonable(x) for x in obj]
    return str(obj)


def prepare_fastapi_intel_payload(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Payload estável para endpoint futuro (apenas normalização de chaves/valores).

    Não inclui bytes, datetime ou tipos custom — use antes de ``JSONResponse``.
    """
    return intel_report_to_jsonable(report)  # type: ignore[return-value]


def prepare_fastapi_batch_payload(batch_report: Dict[str, Any]) -> Dict[str, Any]:
    """Idem ``prepare_fastapi_intel_payload`` para relatórios em lote."""
    return intel_report_to_jsonable(batch_report)  # type: ignore[return-value]
