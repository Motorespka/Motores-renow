"""
Revisão em lote read-only: analisa linhas de motores já existentes sem gravar no Supabase.

Como rodar na prática (Moto-Renow Streamlit):

1. Utilizador admin → página **Diagnóstico** → separador **Motor da oficina**.
2. Secção **Revisão em lote — motor_inteligencia (read-only)** → definir amostra → **Gerar relatório**.
3. Descarregar JSON opcional (payload já passível de API).

Programático (lista de linhas que já tens em memória):

    from services.motor_inteligencia.batch_review import build_batch_review_report
    from services.motor_inteligencia.serialization import prepare_fastapi_batch_payload

    report = build_batch_review_report(rows, limit=200)
    payload = prepare_fastapi_batch_payload(report)

Todas as funções aqui são puras relativamente ao armazenamento: não recebem cliente DB.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple

from services.motor_inteligencia import analyze_motor_technical
from services.motor_inteligencia.coercion import coerce_supabase_motor_row


def _motor_id(row: Dict[str, Any]) -> str:
    mid = row.get("id") if row.get("id") not in (None, "") else row.get("Id")
    return str(mid or "").strip() or "sem_id"


def _motor_label(row: Dict[str, Any]) -> str:
    marca = str(row.get("marca") or row.get("Marca") or "").strip() or "-"
    modelo = str(row.get("modelo") or row.get("Modelo") or "").strip() or "-"
    return f"{marca} | {modelo}"


def analyze_motor_row_readonly(row: Dict[str, Any]) -> Dict[str, Any]:
    """Uma linha Supabase/view → relatório completo ``analyze_motor_technical`` (read-only)."""
    payload = coerce_supabase_motor_row(dict(row))
    return analyze_motor_technical(payload)


def build_batch_review_report(
    rows: Iterable[Dict[str, Any]],
    *,
    limit: int = 300,
    examples_per_bucket: int = 5,
) -> Dict[str, Any]:
    """
    Agrega análises técnicas para calibragem e revisão humana.

    * ``limit``: máximo de linhas processadas (proteção de CPU).
    * ``examples_per_bucket``: quantos exemplos por status (id + rótulo + linha curta).
    """
    rows_list = list(rows)[: max(1, min(int(limit), 5000))]
    total = len(rows_list)

    status_counts: Counter[str] = Counter()
    issue_codes: Counter[str] = Counter()
    warning_codes: Counter[str] = Counter()

    examples: Dict[str, List[Dict[str, Any]]] = {"ok": [], "alerta": [], "critico": [], "insuficiente": []}
    per_motor: List[Dict[str, Any]] = []

    for row in rows_list:
        try:
            rep = analyze_motor_row_readonly(row)
        except Exception as exc:
            status_counts["insuficiente"] += 1
            entry = {
                "motor_id": _motor_id(row),
                "label": _motor_label(row),
                "status": "insuficiente",
                "confidence": 0.0,
                "needs_human_review": True,
                "summary_one_liner": f"Falha ao analisar: {exc}",
                "first_issue": None,
                "first_warning": None,
            }
            per_motor.append(entry)
            if len(examples["insuficiente"]) < examples_per_bucket:
                examples["insuficiente"].append(
                    {"motor_id": entry["motor_id"], "label": entry["label"], "line": entry["summary_one_liner"]}
                )
            continue

        val = rep.get("validation") or {}
        status = str(val.get("status") or "insuficiente")
        status_counts[status] += 1

        for it in val.get("issues") or []:
            c = str(it.get("code") or "issue")
            issue_codes[c] += 1
        for w in val.get("warnings") or []:
            c = str(w.get("code") or "warning")
            warning_codes[c] += 1

        n = rep.get("input_normalized") or {}
        insuf = n.get("insufficient_for") or []

        entry = {
            "motor_id": _motor_id(row),
            "label": _motor_label(row),
            "status": status,
            "confidence": float(val.get("confidence") or 0.0),
            "needs_human_review": bool(val.get("needs_human_review")),
            "summary_one_liner": rep.get("summary_one_liner") or rep.get("summary") or "",
            "first_issue": (val.get("issues") or [{}])[0].get("code") if val.get("issues") else None,
            "first_warning": (val.get("warnings") or [{}])[0].get("code") if val.get("warnings") else None,
            "insufficient_for_count": len(insuf),
            "insufficient_for_top": insuf[:3],
        }
        per_motor.append(entry)

        if status in examples and len(examples[status]) < examples_per_bucket:
            examples[status].append(
                {
                    "motor_id": entry["motor_id"],
                    "label": entry["label"],
                    "line": (entry["summary_one_liner"] or "")[:160],
                }
            )

    def top_counter(cnt: Counter[str], k: int = 8) -> List[Dict[str, Any]]:
        return [{"code": c, "count": n} for c, n in cnt.most_common(k)]

    need_review_sorted = sorted(
        [x for x in per_motor if x.get("needs_human_review")],
        key=lambda x: (-len(str(x.get("first_warning") or "")), -float(x.get("confidence") or 0.0)),
    )[:15]

    confidence_sorted = sorted(per_motor, key=lambda x: (-float(x.get("confidence") or 0.0), x.get("status")))[:15]

    unlock_candidates = sorted(
        [
            x
            for x in per_motor
            if x.get("status") == "insuficiente"
            and 0 < int(x.get("insufficient_for_count") or 0) <= 2
            and not x.get("first_issue")
        ],
        key=lambda x: int(x.get("insufficient_for_count") or 99),
    )[:15]

    return {
        "meta": {
            "total_analisado": total,
            "limite_aplicado": limit,
            "read_only": True,
        },
        "por_status": dict(status_counts),
        "top_issues": top_counter(issue_codes),
        "top_warnings": top_counter(warning_codes),
        "exemplos_por_status": examples,
        "motores_maior_revisao_humana": need_review_sorted,
        "motores_maior_confianca": [x for x in confidence_sorted if x.get("status") == "ok"][:10]
        or confidence_sorted[:10],
        "quase_desbloqueados": unlock_candidates,
    }
