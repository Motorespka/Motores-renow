"""
UI read-only para a camada ``motor_inteligencia`` (badges verde/amarelo/vermelho/cinza).

Não altera dados nem chama persistência — apenas renderiza ``analyze_motor_technical``.
"""

from __future__ import annotations

import html
import json
from typing import Any, Dict

import streamlit as st

from services.motor_inteligencia import analyze_motor_technical, status_to_alert_color
from services.motor_inteligencia.coercion import coerce_supabase_motor_row


def _coerce_payload(raw_or_row: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(raw_or_row, dict) and (
        "dados_tecnicos_json" in raw_or_row
        or "rpm_nominal" in raw_or_row
        or "potencia_hp_cv" in raw_or_row
        or raw_or_row.get("id") is not None
        or raw_or_row.get("Id") is not None
    ):
        return coerce_supabase_motor_row(raw_or_row)
    return raw_or_row


def _badge_html(label: str, status: str) -> str:
    color = status_to_alert_color(status)
    fg = "#ffffff" if status in ("critico", "alerta", "ok") else "#f8fafc"
    return (
        f'<span style="display:inline-block;margin:4px 8px 4px 0;padding:6px 14px;'
        f"border-radius:999px;background:{color};color:{fg};font-weight:600;font-size:0.85rem;"
        f'">{html.escape(label)}: {html.escape(status)}</span>'
    )


def render_intel_consulta_inline(
    raw_or_row: Dict[str, Any],
    *,
    key_prefix: str = "cq_intel",
) -> None:
    """
    Linha mínima para cards na consulta: badge + uma frase; falhas silenciosas (não quebra a lista).
    """
    try:
        report = analyze_motor_technical(_coerce_payload(raw_or_row))
    except Exception:
        return

    val = report.get("validation") or {}
    status = str(val.get("status") or "insuficiente")
    line = str(report.get("summary_one_liner") or report.get("summary") or "").strip()
    if len(line) > 130:
        line = line[:127] + "…"

    st.markdown(
        f'<div class="intel-inline" style="margin:6px 0 2px 0;">{_badge_html("Técnico", status)}</div>',
        unsafe_allow_html=True,
    )
    if line:
        st.caption(line)


def render_motor_inteligencia_panel(
    raw_or_row: Dict[str, Any],
    *,
    key_prefix: str = "mi",
    title: str = "Inteligência técnica (read-only)",
    expanded: bool = False,
) -> None:
    """
    ``raw_or_row``: payload ``dados_tecnicos_json``-like ou linha Supabase (com colunas planas).
    """
    try:
        report = analyze_motor_technical(_coerce_payload(raw_or_row))
    except Exception as exc:
        st.warning(f"Camada técnica indisponível neste momento: {exc}")
        return

    val = report.get("validation") or {}
    status = str(val.get("status") or "insuficiente")
    summary = report.get("summary") or ""
    one_line = str(report.get("summary_one_liner") or "").strip()
    derived = report.get("derived") or {}

    st.subheader(title)
    st.markdown(
        f'<div style="margin-bottom:8px;">{_badge_html("Consistência", status)}</div>',
        unsafe_allow_html=True,
    )
    if val.get("needs_human_review"):
        st.markdown(
            '<span style="color:#ca8a04;font-weight:600;">Revisão humana sugerida</span>',
            unsafe_allow_html=True,
        )
    st.caption(one_line or summary)

    d_line = []
    if derived.get("ns_rpm") is not None:
        d_line.append(f"ns ≈ {derived['ns_rpm']:.1f} rpm")
    if derived.get("slip_percent") is not None:
        d_line.append(f"s ≈ {derived['slip_percent']:.2f} %")
    if derived.get("pin_kw") is not None:
        d_line.append(f"Pin ≈ {derived['pin_kw']:.3f} kW")
    if derived.get("torque_nm") is not None:
        d_line.append(f"T ≈ {derived['torque_nm']:.2f} Nm")
    if d_line:
        st.caption(" · ".join(d_line))

    with st.expander("Detalhe técnico (JSON)", expanded=expanded):
        st.json(
            {
                "validation": val,
                "derived": {k: v for k, v in derived.items() if not str(k).startswith("_")},
                "future_calculations": report.get("future_calculations"),
            },
            expanded=False,
        )
        st.download_button(
            "Baixar relatório técnico (JSON)",
            data=json.dumps(report, ensure_ascii=False, indent=2, default=str),
            file_name=f"{key_prefix}_motor_inteligencia.json",
            mime="application/json",
            key=f"{key_prefix}_dl_intel",
        )
