"""
Assinatura técnica de rebobinagem — comparável entre motores, sem persistência.

Serve para agrupamento, similaridade futura e conferência de cálculo de oficina.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional


def _norm(s: str) -> str:
    t = str(s or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


def _join_nums(nums: Optional[List[int]]) -> str:
    if not nums:
        return ""
    return "-".join(str(n) for n in nums)


def build_rewinding_signature(
    *,
    electric_summary: Dict[str, Any],
    rewinding_normalized: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Monta componentes normalizados e uma string estável para matching aproximado.

    ``electric_summary`` deve conter chaves opcionais: power_kw, rpm_nominal, poles,
    frequency_hz, phases, tensions_v (lista), tipo_motor, carcaca (já resolvidos na análise).
    """
    mr = rewinding_normalized.get("motor_ref") or {}
    pr = rewinding_normalized.get("principal") or {}
    ax = rewinding_normalized.get("auxiliar") or {}
    esq = rewinding_normalized.get("esquema") or {}
    mec = rewinding_normalized.get("mecanica") or {}

    comp: Dict[str, str] = {
        "pot_kw": f"{electric_summary.get('power_kw') or ''}"[:12],
        "rpm": f"{electric_summary.get('rpm_nominal') or ''}"[:12],
        "polos": f"{electric_summary.get('poles') or ''}",
        "fases": _norm(electric_summary.get("phases") or mr.get("fases")),
        "tensao": ",".join(str(x) for x in (electric_summary.get("tensions_v") or [])[:4])[:40],
        "tipo_motor": _norm(electric_summary.get("tipo_motor") or mr.get("tipo_motor")),
        "carcaca": _norm(mr.get("carcaca")),
        "ranhuras": f"{(esq.get('ranhuras') or {}).get('value') or ''}",
        "passo_pr": _join_nums((pr.get("passos") or {}).get("numbers")),
        "espiras_pr": _join_nums((pr.get("espiras") or {}).get("numbers")),
        "fio_pr": _norm(str((pr.get("fios") or {}).get("gauge_token") or "")),
        "passo_ax": _join_nums((ax.get("passos") or {}).get("numbers")),
        "espiras_ax": _join_nums((ax.get("espiras") or {}).get("numbers")),
        "fio_ax": _norm(str((ax.get("fios") or {}).get("gauge_token") or "")),
        "pacote_mm": f"{(mec.get('pacote_mm') or {}).get('value_mm') or ''}"[:12],
        "diam_mm": f"{(mec.get('diametro_mm') or {}).get('value_mm') or ''}"[:12],
    }
    sig_str = "|".join(f"{k}={v}" for k, v in sorted(comp.items()) if v)
    digest = hashlib.sha256(sig_str.encode("utf-8")).hexdigest()[:16] if sig_str else ""

    return {
        "components": comp,
        "signature_string": sig_str,
        "signature_digest": digest,
    }


def prepare_similarity_query(signature: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estrutura pronta para futura busca por motores semelhantes (sem I/O).

    O motor de similaridade real usará ``components`` + tolerâncias de RPM/polos/etc.
    """
    comp = signature.get("components") or {}
    return {
        "must_match_soft": ["polos", "fases", "tensao"],
        "must_match_numeric_tolerance": {"rpm": 0.04, "pot_kw": 0.15},
        "rewinding_keys": ["ranhuras", "passo_pr", "espiras_pr", "fio_pr", "passo_ax", "espiras_ax", "fio_ax"],
        "geometry_keys": ["pacote_mm", "diam_mm", "carcaca"],
        "payload": comp,
    }
