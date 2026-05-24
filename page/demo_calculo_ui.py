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
          <div class="dt-hero__brand">
            <span class="dt-hero__logo">PMTH</span>
            <span class="dt-hero__sys">SYS OPERACIONAL</span>
          </div>
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


MSG_SUGESTAO_BLOQUEADA = "Nenhuma (Limites físicos excedidos)"
MSG_PROJETO_INVIAVEL = (
    "PROJETO INVIÁVEL: O motor não passou nos limites físicos obrigatórios "
    "(Risco de Saturação ou Fator de Enchimento). Nenhuma configuração foi recomendada."
)
MSG_PROJETO_INVIAVEL_UI = (
    "🚨 PROJETO INVIÁVEL: Limites físicos (Saturação ou Fator de Enchimento) foram excedidos. "
    "Nenhuma configuração sugerida."
)
KPI_NA = "—"

from engine.physics_audit import cenario_valido_para_painel_recomendado  # re-export UI


def optimizer_has_cenarios(opt_data: Optional[dict[str, Any]]) -> bool:
    """Modo otimizador A/B/C ativo (session com cenários calculados)."""
    return bool(opt_data and opt_data.get("cenarios"))


def _find_optimizer_scenario(
    opt_data: dict[str, Any], cenario_id: str
) -> Optional[dict[str, Any]]:
    for cen in opt_data.get("cenarios") or []:
        if str(cen.get("cenario_id")) == cenario_id:
            return cen
    return None


def resolve_cenario_recomendado_raw(
    opt_data: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Cenário indicado pelo backend (id em cenario_recomendado), sem filtro visual."""
    if not optimizer_has_cenarios(opt_data):
        return None
    rec_id = str(opt_data.get("cenario_recomendado") or "B").strip() or "B"
    return _find_optimizer_scenario(opt_data, rec_id)


def _cenario_abort_reason_blob(cenario: dict[str, Any]) -> str:
    parts = [str(cenario.get("abort_reason", "") or "")]
    parts.extend(str(a) for a in (cenario.get("alertas") or []))
    return " ".join(parts)


def is_projeto_inviavel_nuclear(
    cenario_recomendado: Optional[dict[str, Any]],
) -> bool:
    """Trava visual estrita (abort_reason + alertas) — usada no painel de resultados."""
    if cenario_recomendado is None:
        return True
    abort_txt = _cenario_abort_reason_blob(cenario_recomendado)
    from engine.physics_audit import normalize_fill_factor_ff

    ff = normalize_fill_factor_ff(cenario_recomendado.get("fill_factor_ff", 0)) or 0.0
    try:
        conf = int(cenario_recomendado.get("physics_confidence", 0) or 0)
    except (TypeError, ValueError):
        conf = 0
    return (
        conf == 0
        or ff > 0.45
        or "Risco Severo de Saturação" in abort_txt
        or "Cálculo Abortado" in abort_txt
    )


def is_cenario_inviavel_visual(
    cenario_recomendado: Optional[dict[str, Any]],
) -> bool:
    """Trava de segurança visual — espelha o gate do painel ★ e alertas de aborto."""
    return is_projeto_inviavel_nuclear(cenario_recomendado)


def resolve_recommended_optimizer_scenario(
    opt_data: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Cenário ★ aprovado pelo gate visual estrito. None = nenhum apto."""
    if not optimizer_has_cenarios(opt_data):
        return None

    from engine.physics_audit import cenario_valido_para_painel_recomendado

    rec_id = str(opt_data.get("cenario_recomendado") or "").strip()
    if rec_id:
        cen = _find_optimizer_scenario(opt_data, rec_id)
        if cenario_valido_para_painel_recomendado(cen):
            return cen

    for cid in ("B", "C", "A"):
        cen = _find_optimizer_scenario(opt_data, cid)
        if cenario_valido_para_painel_recomendado(cen):
            return cen
    return None


def projeto_fisicamente_aprovado(opt_data: Optional[dict[str, Any]]) -> bool:
    if not optimizer_has_cenarios(opt_data):
        return False
    return resolve_recommended_optimizer_scenario(opt_data) is not None


def is_projeto_inviavel(
    opt_data: Optional[dict[str, Any]],
    *,
    twin_data: Optional[dict[str, Any]] = None,
) -> bool:
    """Modo A/B/C: inviável conforme cenário bruto retornado pelo backend."""
    _ = twin_data
    if not optimizer_has_cenarios(opt_data):
        return False
    return is_cenario_inviavel_visual(resolve_cenario_recomendado_raw(opt_data))


def render_projeto_inviavel_alert() -> None:
    st.error(MSG_PROJETO_INVIAVEL_UI)


def render_painel_cenario_recomendado(
    opt_data: Optional[dict[str, Any]],
    *,
    twin_data: Optional[dict[str, Any]] = None,
) -> bool:
    """
    Desenha o painel ★ Cenário recomendado.
    Modo A/B/C: NUNCA usa twin_data. Retorna True se exibiu sugestão válida.
    """
    _ = twin_data
    panel_title("Cenário recomendado (★)")

    if optimizer_has_cenarios(opt_data):
        rec = resolve_recommended_optimizer_scenario(opt_data)
        if not rec or not cenario_valido_para_painel_recomendado(rec):
            st.error(MSG_PROJETO_INVIAVEL_UI)
            return False
        conf = int(rec.get("physics_confidence") or rec.get("confidence_score") or 0)
        if conf <= 0:
            st.error(MSG_PROJETO_INVIAVEL_UI)
            return False
        render_kpi_row(
            espiras=rec.get("espiras", KPI_NA),
            bitola=rec.get("fio_texto") or rec.get("calibre_display") or KPI_NA,
            confianca=int(rec.get("physics_confidence") or rec.get("confidence_score") or 0),
            ocupacao=rec.get("fator_ocupacao_ranhura"),
        )
        st.caption(
            f"Fonte: otimizador A/B/C — cenário **{rec.get('cenario_id')}** "
            f"(veto FEM + bitola por ff)."
        )
        return True

    return False


def pick_primary_candidate(
    twin_data: Optional[dict[str, Any]],
    opt_data: Optional[dict[str, Any]],
) -> tuple[Any, Any, int, Optional[float], Optional[str]]:
    """
    KPI do relatório executivo. Modo A/B/C: somente cenário validado; sem twin/res bruto.
    """
    if optimizer_has_cenarios(opt_data):
        rec = resolve_recommended_optimizer_scenario(opt_data)
        if rec is not None:
            return (
                rec.get("espiras"),
                rec.get("fio_texto") or rec.get("calibre_display") or KPI_NA,
                int(rec.get("physics_confidence") or rec.get("confidence_score") or 0),
                rec.get("fator_ocupacao_ranhura"),
                None,
            )
        return KPI_NA, KPI_NA, 0, None, "red"

    return KPI_NA, KPI_NA, 0, None, None
