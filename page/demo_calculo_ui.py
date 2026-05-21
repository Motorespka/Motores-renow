#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Componentes visuais premium — Gêmeo Digital / Demo Cálculo."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Optional

import streamlit as st
import streamlit.components.v1 as components

_REPO = Path(__file__).resolve().parents[1]
_CSS_PATH = _REPO / "assets" / "demo_calculo_dashboard.css"


def inject_dashboard_css() -> None:
    if st.session_state.get("_demo_dt_css_loaded"):
        return
    base = _CSS_PATH.read_text(encoding="utf-8") if _CSS_PATH.is_file() else ""
    overrides = """
    .demo-twin-dashboard ~ div [data-testid="stAppViewContainer"],
    .demo-twin-dashboard { color: #e6edf3; }
    [data-testid="stMetricValue"] { font-family: "JetBrains Mono", monospace; }
    """
    st.markdown(
        f"<style>{base}\n{overrides}</style>",
        unsafe_allow_html=True,
    )
    st.session_state["_demo_dt_css_loaded"] = True


def open_dashboard_shell() -> None:
    inject_dashboard_css()
    st.markdown('<div class="demo-twin-dashboard">', unsafe_allow_html=True)


def close_dashboard_shell() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_hero(*, subtitle: str = "") -> None:
    sub = subtitle or (
        "Motor PINN · visão computacional · FEM WEG/IEC · auditoria física em tempo real"
    )
    st.markdown(
        f"""
        <div class="dt-hero">
          <h1>GÊMEO DIGITAL DE MOTORES</h1>
          <p>{html.escape(sub)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_title(text: str) -> None:
    st.markdown(f'<p class="dt-panel-title">{html.escape(text)}</p>', unsafe_allow_html=True)


def confidence_tier(score: int) -> str:
    if score > 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def confidence_badge_html(score: int) -> str:
    tier = confidence_tier(score)
    cls = {"green": "dt-badge-ok", "yellow": "dt-badge-warn", "red": "dt-badge-danger"}[tier]
    return f'<span class="dt-badge {cls}">{int(score)}%</span>'


def render_critical_alert(message: str, *, b_tesla: Optional[float] = None) -> None:
    """Alerta vermelho de abort (saturação B > 1.8 T)."""
    extra = ""
    if b_tesla is not None:
        extra = f' <span style="color:#8b949e;font-size:0.85rem;">(B ≈ {b_tesla:.2f} T)</span>'
    st.markdown(
        f"""
        <div class="dt-alert-abort">
          <strong>⛔ {html.escape(message)}</strong>{extra}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.error(message)


def render_vision_manual_warning() -> None:
    from page.demo_calculo_validation import MSG_VISAO_UI

    st.warning(MSG_VISAO_UI)


def render_kpi_row(
    *,
    espiras: Any = "—",
    bitola: Any = "—",
    confianca: int = 0,
    ocupacao: Any = None,
    force_tier: Optional[str] = None,
) -> None:
    tier = force_tier or confidence_tier(confianca)
    occ_txt = f"{ocupacao}%" if ocupacao is not None else ""
    st.markdown(
        f"""
        <div class="dt-kpi-row">
          <div class="dt-kpi">
            <span class="dt-kpi-label">Espiras / bobina</span>
            <span class="dt-kpi-value" style="color:#e6edf3">{html.escape(str(espiras))}</span>
          </div>
          <div class="dt-kpi">
            <span class="dt-kpi-label">Bitola (AWG)</span>
            <span class="dt-kpi-value" style="color:#deff9a">{html.escape(str(bitola))}</span>
          </div>
          <div class="dt-kpi dt-kpi-{tier}">
            <span class="dt-kpi-label">Confiança física</span>
            <span class="dt-kpi-value">{int(confianca)}%</span>
          </div>
        </div>
        """
        + (f'<p style="color:#8b949e;font-size:0.8rem;margin:-0.5rem 0 0.75rem 0;">Ocupação ranhura: {html.escape(occ_txt)}</p>' if occ_txt else ""),
        unsafe_allow_html=True,
    )


def render_candidates_table(candidatos: list[dict[str, Any]]) -> None:
    if not candidatos:
        return
    rows = []
    for c in candidatos:
        score = int(c.get("confianca_pct") or 0)
        ff = (c.get("ocupacao_ff") or 0) * 100
        j = c.get("densidade_j")
        j_txt = f"{j:.2f}" if j is not None else "—"
        rows.append(
            "<tr>"
            f"<td><strong>{html.escape(str(c.get('opcao', '')))}</strong></td>"
            f"<td>{html.escape(str(c.get('espiras_por_bobina', '—')))}</td>"
            f"<td>{html.escape(str(c.get('descricao', '—')))}</td>"
            f"<td>{j_txt}</td>"
            f"<td>{ff:.1f}%</td>"
            f"<td>{confidence_badge_html(score)}</td>"
            "</tr>"
        )
    st.markdown(
        """
        <table class="dt-table">
          <thead><tr>
            <th>Opção</th><th>Espiras</th><th>Fio</th>
            <th>J (A/mm²)</th><th>ff</th><th>Confiança</th>
          </tr></thead>
          <tbody>
        """
        + "".join(rows)
        + "</tbody></table>",
        unsafe_allow_html=True,
    )


def render_empty_report(message: str) -> None:
    st.markdown(
        f'<div class="dt-empty-state"><p>{html.escape(message)}</p></div>',
        unsafe_allow_html=True,
    )


def render_mermaid_dark(diagram: str, *, height: int = 300, title: str = "") -> None:
    if not diagram or not diagram.strip():
        return
    body = diagram.strip()
    if title:
        st.markdown(f"**{title}**")
    st.markdown('<div class="dt-mermaid-wrap">', unsafe_allow_html=True)
    html_doc = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"/>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
mermaid.initialize({{
  startOnLoad: true,
  theme: 'dark',
  themeVariables: {{
    primaryColor: '#1c2128',
    primaryTextColor: '#deff9a',
    primaryBorderColor: '#deff9a',
    lineColor: '#8b949e',
    secondaryColor: '#161b22',
    tertiaryColor: '#0e1117'
  }}
}});
</script>
<style>body{{margin:0;background:#0d1117;}} .mermaid{{background:#0d1117;}}</style>
</head><body><div class="mermaid">{body}</div></body></html>"""
    components.html(html_doc, height=height, scrolling=False)
    st.markdown("</div>", unsafe_allow_html=True)


def render_checklist(items: list[str]) -> None:
    if not items:
        return
    st.warning("Checklist — medições pendentes")
    for item in items:
        st.markdown(f"- [ ] {item}")


def pick_primary_candidate(
    twin_data: Optional[dict[str, Any]],
    opt_data: Optional[dict[str, Any]],
) -> tuple[Any, Any, int, Optional[float], Optional[str]]:
    """Retorna (espiras, bitola, confiança, ocupação, force_tier) para KPI."""
    if twin_data and twin_data.get("saturacao_abortada"):
        cands = twin_data.get("candidatos") or []
        sus = next((c for c in cands if c.get("opcao") == "SUSPEITO"), cands[0] if cands else {})
        return (
            sus.get("espiras_por_bobina", "—"),
            sus.get("descricao", "—"),
            0,
            (sus.get("ocupacao_ff") or 0) * 100 if sus.get("ocupacao_ff") else None,
            "red",
        )
    if twin_data and twin_data.get("candidatos"):
        cands = twin_data["candidatos"]
        best = max(cands, key=lambda c: int(c.get("confianca_pct") or 0))
        desc = best.get("descricao") or f"{best.get('fio_awg')} AWG"
        return (
            best.get("espiras_por_bobina"),
            desc,
            int(best.get("confianca_pct") or 0),
            (best.get("ocupacao_ff") or 0) * 100,
            None,
        )
    if opt_data and opt_data.get("cenarios"):
        rec = str(opt_data.get("cenario_recomendado") or "B")
        cen = next(
            (c for c in opt_data["cenarios"] if str(c.get("cenario_id")) == rec),
            opt_data["cenarios"][0],
        )
        score = int(cen.get("physics_confidence") or cen.get("confidence_score") or 0)
        fio = cen.get("fio_texto") or cen.get("calibre_display") or "—"
        return (
            cen.get("espiras"),
            fio,
            score,
            cen.get("fator_ocupacao_ranhura"),
            None,
        )
    return "—", "—", 0, None, None
