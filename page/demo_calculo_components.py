#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Componentes HTML premium — Gêmeo Digital (espelho do mockup PMTH)."""

from __future__ import annotations

import html
import json
import math
from pathlib import Path
from typing import Any, Optional

import streamlit as st

from engine.physics_validator import PhysicsValidator

_REPO = Path(__file__).resolve().parents[1]
_TOKENS_PATH = _REPO / "design-system" / "digital-twin-tokens.json"


def load_design_tokens() -> dict[str, Any]:
    if _TOKENS_PATH.is_file():
        return json.loads(_TOKENS_PATH.read_text(encoding="utf-8"))
    return {}


def _esc(s: Any) -> str:
    return html.escape(str(s) if s is not None else "")


def _zone_status(
    value: Optional[float],
    ideal_lo: float,
    ideal_hi: float,
    hard_lo: Optional[float] = None,
    hard_hi: Optional[float] = None,
) -> str:
    if value is None:
        return "muted"
    if hard_lo is not None and value < hard_lo:
        return "danger"
    if hard_hi is not None and value > hard_hi:
        return "danger"
    if ideal_lo <= value <= ideal_hi:
        return "ok"
    return "warn"


def render_verdict_banner(
    *,
    aprovado: bool,
    confianca_pct: float,
    desvio_pct: Optional[float] = None,
    espiras: Any = "—",
    bitola: Any = "—",
    lt_mm: Any = None,
    subtitulo: str = "",
) -> None:
    """Banner superior — APROVADO / REPROVADO (mockup PMTH)."""
    status = "ok" if aprovado else "danger"
    titulo = (
        "APROVADO — dentro da faixa OFICIAL"
        if aprovado
        else "REPROVADO — limites físicos excedidos"
    )
    icon = "✓" if aprovado else "✕"
    desvio_txt = f"desvio médio ±{desvio_pct:.1f}%" if desvio_pct is not None else ""
    lt_txt = f"{lt_mm} mm" if lt_mm is not None else "—"
    sub = subtitulo or (
        f"Confiança física {confianca_pct:.1f}%"
        + (f" · {desvio_txt}" if desvio_txt else "")
    )
    st.markdown(
        f"""
        <div class="dt-verdict dt-verdict--{status}">
          <div class="dt-verdict__icon">{icon}</div>
          <div class="dt-verdict__body">
            <div class="dt-verdict__title">{_esc(titulo)}</div>
            <div class="dt-verdict__sub">{_esc(sub)}</div>
          </div>
          <div class="dt-verdict__metrics">
            <div class="dt-verdict__metric">
              <span class="dt-verdict__metric-label">ESPIRAS / BOBINA</span>
              <span class="dt-verdict__metric-value">{_esc(espiras)}</span>
            </div>
            <div class="dt-verdict__metric">
              <span class="dt-verdict__metric-label">BITOLA SUGERIDA</span>
              <span class="dt-verdict__metric-value dt-verdict__metric-value--accent">{_esc(bitola)}</span>
            </div>
            <div class="dt-verdict__metric">
              <span class="dt-verdict__metric-label">LT</span>
              <span class="dt-verdict__metric-value">{_esc(lt_txt)}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="dt-section-head">
          <span class="dt-section-head__title">{_esc(title)}</span>
          {f'<span class="dt-section-head__sub">{_esc(subtitle)}</span>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _arc_gauge_svg(
    *,
    label: str,
    value: float,
    max_value: float,
    unit: str,
    status: str,
    size: int = 148,
) -> str:
    """Gauge semicircular estilo mockup."""
    pct = min(1.0, max(0.0, value / max_value)) if max_value > 0 else 0.0
    cx, cy, r = size / 2, size * 0.58, size * 0.38
    start_angle = math.pi
    end_angle = math.pi * (1.0 - pct)
    x1 = cx + r * math.cos(start_angle)
    y1 = cy - r * math.sin(start_angle)
    x2 = cx + r * math.cos(end_angle)
    y2 = cy - r * math.sin(end_angle)
    large_arc = 1 if pct > 0.5 else 0
    color = {
        "ok": "#3fb950",
        "warn": "#ff8a00",
        "danger": "#f85149",
        "muted": "#6b8499",
    }.get(status, "#00e5ff")
    track = "rgba(0,229,255,0.12)"
    display = f"{value:.2f}{unit}".strip()
    return f"""
    <div class="dt-arc-gauge dt-arc-gauge--{status}">
      <svg viewBox="0 0 {size} {size * 0.72}" width="{size}" height="{int(size * 0.72)}" aria-hidden="true">
        <path d="M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}"
              fill="none" stroke="{track}" stroke-width="10" stroke-linecap="round"/>
        <path d="M {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2}"
              fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"
              style="filter: drop-shadow(0 0 6px {color}88)"/>
      </svg>
      <div class="dt-arc-gauge__value">{_esc(display)}</div>
      <div class="dt-arc-gauge__label">{_esc(label)}</div>
    </div>
    """


def render_arc_gauge_row(
    *,
    j_val: Optional[float],
    ff_val: Optional[float],
    b_val: Optional[float],
) -> None:
    pv = PhysicsValidator
    j = j_val or 0.0
    ff_pct = (ff_val or 0.0) * 100.0
    b = b_val or 0.0
    gauges = [
        (
            "Densidade de Corrente [J]",
            j,
            8.0,
            " A/mm²",
            _zone_status(j_val, pv.LIMITE_J_MIN, pv.LIMITE_J_IDEAL + 1.0, hard_hi=pv.LIMITE_J_MAX),
        ),
        (
            "Fator de Enchimento [ff]",
            ff_pct,
            50.0,
            " ff",
            _zone_status(
                ff_val,
                pv.LIMITE_FF_IDEAL_LO,
                pv.LIMITE_FF_IDEAL_HI,
                hard_lo=pv.LIMITE_FF_MIN,
                hard_hi=pv.LIMITE_FF_MAX,
            ),
        ),
        (
            "Saturação Magnética [B]",
            b,
            2.0,
            " T",
            _zone_status(b_val, 0.0, pv.LIMITE_B, hard_hi=1.8),
        ),
    ]
    parts = [
        _arc_gauge_svg(
            label=label,
            value=val,
            max_value=max_v,
            unit=unit,
            status=status,
        )
        for label, val, max_v, unit, status in gauges
    ]
    st.markdown(
        f'<div class="dt-gauge-row">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def render_metric_bar(
    label: str,
    value: Optional[float],
    max_val: float,
    *,
    unit: str = "",
    status: str = "ok",
) -> None:
    if value is None:
        st.caption(f"{label}: —")
        return
    ratio = min(1.0, max(0.0, float(value) / max_val)) if max_val > 0 else 0.0
    pct = int(ratio * 100)
    st.markdown(
        f"""
        <div class="dt-metric-bar dt-metric-bar--{status}">
          <div class="dt-metric-bar__head">
            <span>{_esc(label)}</span>
            <span class="dt-metric-bar__vals">{value:.2f}{_esc(unit)} / {max_val:.2f}{_esc(unit)}</span>
          </div>
          <div class="dt-metric-bar__track">
            <div class="dt-metric-bar__fill" style="width:{pct}%"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_kpi_row(
    *,
    torque_nm: Optional[float] = None,
    rendimento_pct: Optional[float] = None,
    delta_temp_c: Optional[float] = None,
) -> None:
    """KPIs inferiores (placeholders quando FEM não disponível)."""
    cards = []
    items = [
        ("Torque Nominal", torque_nm, "N·m", "+2.1%", "ok"),
        ("Rendimento", rendimento_pct, "%", "+0.4%", "ok"),
        ("Δ Temp.", delta_temp_c, "°C", "-3.8%", "warn"),
    ]
    for title, val, unit, delta, tier in items:
        if val is None:
            val_txt = "—"
        else:
            val_txt = f"{val:.1f} {unit}"
        cards.append(
            f"""
            <div class="dt-mini-kpi dt-mini-kpi--{tier}">
              <div class="dt-mini-kpi__label">{_esc(title)}</div>
              <div class="dt-mini-kpi__value">{_esc(val_txt)}</div>
              <div class="dt-mini-kpi__delta">{_esc(delta)}</div>
            </div>
            """
        )
    st.markdown(f'<div class="dt-mini-kpi-row">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_compare_column(
    *,
    side: str,
    snapshot_title: str,
    espiras: Any,
    fio: str,
    j_val: Optional[float],
    ff_val: Optional[float],
    badge: str = "",
) -> str:
    pv = PhysicsValidator
    j_status = _zone_status(
        j_val, pv.LIMITE_J_MIN, pv.LIMITE_J_IDEAL + 1.0, hard_hi=pv.LIMITE_J_MAX
    )
    ff_status = _zone_status(
        ff_val,
        pv.LIMITE_FF_IDEAL_LO,
        pv.LIMITE_FF_IDEAL_HI,
        hard_lo=pv.LIMITE_FF_MIN,
        hard_hi=pv.LIMITE_FF_MAX,
    )
    j_pct = (
        int(min(100, max(0, (j_val or 0) / pv.LIMITE_J_MAX * 100)))
        if j_val is not None
        else 0
    )
    ff_pct = (
        int(min(100, max(0, (ff_val or 0) / pv.LIMITE_FF_MAX * 100)))
        if ff_val is not None
        else 0
    )
    ff_disp = f"{(ff_val or 0) * 100:.1f}%" if ff_val is not None else "—"
    j_disp = f"{j_val:.2f} A/mm²" if j_val is not None else "—"
    return f"""
    <div class="dt-compare-col dt-compare-col--{side}">
      <div class="dt-compare-col__badge">{_esc(badge)}</div>
      <div class="dt-compare-col__title">{_esc(snapshot_title)}</div>
      <div class="dt-compare-stat"><span>Espiras</span><strong>{_esc(espiras)}</strong></div>
      <div class="dt-compare-stat"><span>Bitola</span><strong>{_esc(fio)}</strong></div>
      <div class="dt-compare-bar dt-compare-bar--{j_status}">
        <div class="dt-compare-bar__label">J · densidade</div>
        <div class="dt-compare-bar__track"><div style="width:{j_pct}%"></div></div>
        <div class="dt-compare-bar__val">{_esc(j_disp)}</div>
      </div>
      <div class="dt-compare-bar dt-compare-bar--{ff_status}">
        <div class="dt-compare-bar__label">ff · enchimento</div>
        <div class="dt-compare-bar__track"><div style="width:{ff_pct}%"></div></div>
        <div class="dt-compare-bar__val">{_esc(ff_disp)}</div>
      </div>
    </div>
    """


def render_compare_grid(html_a: str, html_b: str) -> None:
    st.markdown(
        f'<div class="dt-compare-grid">{html_a}{html_b}</div>',
        unsafe_allow_html=True,
    )


def render_material_card(material_rows: list[dict[str, str]], peso_kg: float) -> None:
    rows_html = "".join(
        f"<tr><td>{_esc(r.get('Item',''))}</td>"
        f"<td>{_esc(r.get('Especificação',''))}</td>"
        f"<td class='dt-mat-qty'>{_esc(r.get('Quantidade',''))}</td></tr>"
        for r in material_rows
    )
    st.markdown(
        f"""
        <div class="dt-material-card">
          <div class="dt-material-card__head">
            <span>Material estimado</span>
            <strong>{peso_kg:.2f} kg</strong> cobre
          </div>
          <table class="dt-table dt-table--compact">
            <thead><tr><th>Item</th><th>Especificação</th><th>Qtd.</th></tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_chip(aprovado: bool, diagnostico: str) -> None:
    cls = "ok" if aprovado else "danger"
    label = "APROVADO" if aprovado else "REPROVADO"
    st.markdown(
        f"""
        <div class="dt-status-chip dt-status-chip--{cls}">
          <span class="dt-status-chip__dot"></span>
          <span><strong>{label}</strong> — {_esc(diagnostico)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
