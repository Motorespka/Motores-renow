#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico físico — comparativo antes/depois, gauges J/ff/B, inventário de cobre.
Consome PhysicsValidator sem alterar sua lógica.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import streamlit as st

from engine.copper_inventory import estimate_copper_from_winding
from engine.physics_audit import estimate_operating_flux_density_t
from engine.physics_validator import PhysicsValidator, PhysicsValidatorEngine
from page.demo_calculo_components import (
    render_arc_gauge_row,
    render_compare_column,
    render_compare_grid,
    render_insight_kpi_row,
    render_material_card,
    render_metric_bar,
    render_section_header,
    render_status_chip,
)
from page.demo_calculo_ui import resolve_recommended_optimizer_scenario


@dataclass
class WindingSnapshot:
    titulo: str
    espiras: Optional[float] = None
    awg: Optional[float] = None
    fio_texto: str = "—"
    j_a_mm2: Optional[float] = None
    ff: Optional[float] = None
    b_tesla: Optional[float] = None
    confianca: int = 0
    paralelos: int = 1


def _parse_awg(raw: Any) -> Optional[float]:
    if raw is None or raw == "":
        return None
    try:
        return float(str(raw).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def _parse_espiras(raw: Any) -> Optional[float]:
    if raw is None or raw == "":
        return None
    try:
        return float(str(raw).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def _wire_from_cenario(cen: dict[str, Any]) -> tuple[Optional[float], int, str]:
    wire = cen.get("wire") or {}
    awg: Optional[float] = None
    par = 1
    if isinstance(wire, dict):
        try:
            awg = float(wire.get("awg"))
            par = int(wire.get("parallel_count") or 1)
        except (TypeError, ValueError):
            awg = None
    fio = str(cen.get("fio_texto") or cen.get("calibre_display") or "—")
    return awg, par, fio


def _metrics_for_winding(
    *,
    espiras: Optional[float],
    awg: Optional[float],
    parallel_count: int,
    ff: Optional[float],
    j_val: Optional[float],
    entrada: dict[str, Any],
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    d = float(entrada.get("diametro_mm") or entrada.get("diametro") or 80)
    p = float(entrada.get("pacote_mm") or entrada.get("pacote") or 70)
    pol = entrada.get("polos")
    pol_i = int(pol) if pol else None
    b_t: Optional[float] = None
    if espiras and espiras > 0:
        b_t = estimate_operating_flux_density_t(
            float(espiras), d, p, pol_i,
            voltage_v=float(entrada.get("tensao_v") or entrada.get("voltagem") or 220),
        )
    return ff, j_val, b_t


def resolve_original_snapshot(
    entrada: dict[str, Any],
    twin_data: Optional[dict[str, Any]] = None,
) -> WindingSnapshot:
    """Coluna A — motor original / sucata (dados informados pelo rebobinador)."""
    esp = _parse_espiras(entrada.get("espiras_engenheiro") or entrada.get("espiras"))
    awg = _parse_awg(entrada.get("fio_engenheiro") or entrada.get("fio_awg"))
    fio_txt = str(entrada.get("fio_engenheiro") or entrada.get("fio_awg") or "—")
    j_val: Optional[float] = None
    ff_val: Optional[float] = None
    conf = 0

    if twin_data and twin_data.get("candidatos"):
        for c in twin_data["candidatos"]:
            if str(c.get("opcao", "")).upper() in ("SUSPEITO", "ORIGINAL", "A"):
                esp = esp or c.get("espiras_por_bobina")
                j_val = c.get("densidade_j")
                ff_val = c.get("ocupacao_ff")
                conf = int(c.get("confianca_pct") or 0)
                fio_txt = str(c.get("descricao") or fio_txt)
                if awg is None and c.get("fio_awg") is not None:
                    awg = float(c.get("fio_awg"))
                break

    ff_val, j_val, b_t = _metrics_for_winding(
        espiras=esp,
        awg=awg,
        parallel_count=1,
        ff=ff_val,
        j_val=j_val,
        entrada=entrada,
    )
    return WindingSnapshot(
        titulo="Original (sucata / informado)",
        espiras=esp,
        awg=awg,
        fio_texto=fio_txt,
        j_a_mm2=j_val,
        ff=ff_val,
        b_tesla=b_t,
        confianca=conf,
    )


def resolve_proposed_snapshot(
    *,
    entrada: dict[str, Any],
    opt_data: Optional[dict[str, Any]],
    twin_data: Optional[dict[str, Any]],
    res: Optional[dict[str, Any]],
) -> Optional[WindingSnapshot]:
    """Coluna B — proposta de rebobinagem (cenário aprovado ou candidato)."""
    if opt_data and opt_data.get("cenarios"):
        cen = resolve_recommended_optimizer_scenario(opt_data)
        if cen is None:
            for c in opt_data["cenarios"]:
                if str(c.get("cenario_id")) == "B":
                    cen = c
                    break
            if cen is None:
                cen = opt_data["cenarios"][0]
        awg, par, fio = _wire_from_cenario(cen)
        esp = cen.get("espiras")
        ff = cen.get("fill_factor_ff")
        j_val = cen.get("current_density_j")
        conf = int(cen.get("physics_confidence") or cen.get("confidence_score") or 0)
        ff, j_val, b_t = _metrics_for_winding(
            espiras=_parse_espiras(esp),
            awg=awg,
            parallel_count=par,
            ff=float(ff) if ff is not None else None,
            j_val=float(j_val) if j_val is not None else None,
            entrada=entrada,
        )
        return WindingSnapshot(
            titulo="Proposta (rebobinagem)",
            espiras=_parse_espiras(esp),
            awg=awg,
            fio_texto=fio,
            j_a_mm2=j_val,
            ff=ff,
            b_tesla=b_t,
            confianca=conf,
            paralelos=par,
        )

    if twin_data and twin_data.get("candidatos"):
        cand = None
        for c in twin_data["candidatos"]:
            if str(c.get("opcao", "")).upper() in ("CORRIGIDO", "B", "PROPOSTA"):
                cand = c
                break
        if cand is None and len(twin_data["candidatos"]) > 1:
            cand = twin_data["candidatos"][-1]
        elif cand is None:
            cand = twin_data["candidatos"][0]
        if cand:
            awg = float(cand.get("fio_awg") or 19)
            esp = cand.get("espiras_por_bobina")
            ff = cand.get("ocupacao_ff")
            j_val = cand.get("densidade_j")
            ff, j_val, b_t = _metrics_for_winding(
                espiras=_parse_espiras(esp),
                awg=awg,
                parallel_count=int(cand.get("paralelo") or 1),
                ff=float(ff) if ff is not None else None,
                j_val=float(j_val) if j_val is not None else None,
                entrada=entrada,
            )
            return WindingSnapshot(
                titulo="Proposta (rebobinagem)",
                espiras=_parse_espiras(esp),
                awg=awg,
                fio_texto=str(cand.get("descricao") or "—"),
                j_a_mm2=j_val,
                ff=ff,
                b_tesla=b_t,
                confianca=int(cand.get("confianca_pct") or 0),
                paralelos=int(cand.get("paralelo") or 1),
            )

    if res and res.get("sugestao_espira"):
        esp = res.get("sugestao_espira")
        awg = res.get("sugestao_fio_awg")
        return WindingSnapshot(
            titulo="Proposta (rebobinagem)",
            espiras=_parse_espiras(esp),
            awg=_parse_awg(awg),
            fio_texto=str(res.get("sugestao_fio_texto") or "—"),
        )
    return None


def build_physics_verdict(
    original: WindingSnapshot,
    proposed: WindingSnapshot,
) -> Any:
    """Veredito PhysicsValidatorEngine sobre a proposta."""
    awg_ref = original.awg if original.awg and proposed.awg else None
    return PhysicsValidatorEngine.validate_scenario_render(
        espiras=float(proposed.espiras or 0),
        awg=float(proposed.awg or 19),
        parallel_count=proposed.paralelos,
        fill_factor_ff=proposed.ff,
        current_density_j=proposed.j_a_mm2,
        b_tesla=proposed.b_tesla,
        awg_referencia=awg_ref,
        espiras_referencia=original.espiras,
        strict_j=bool(proposed.j_a_mm2),
        validate_j=bool(proposed.j_a_mm2),
    )


def render_comparative_side_by_side(
    original: WindingSnapshot,
    proposed: WindingSnapshot,
) -> None:
    """Modo comparativo A/B — layout PMTH."""
    html_a = render_compare_column(
        side="a",
        snapshot_title=original.titulo,
        espiras=original.espiras or "—",
        fio=original.fio_texto,
        j_val=original.j_a_mm2,
        ff_val=original.ff,
        badge="Coluna A — Original",
    )
    html_b = render_compare_column(
        side="b",
        snapshot_title=proposed.titulo,
        espiras=proposed.espiras or "—",
        fio=proposed.fio_texto,
        j_val=proposed.j_a_mm2,
        ff_val=proposed.ff,
        badge="Coluna B — Proposta",
    )
    render_compare_grid(html_a, html_b)


def render_physics_insights_panel(proposed: WindingSnapshot) -> None:
    """Painel Insights Físicos — gauges SVG + barras (mockup PMTH)."""
    pv = PhysicsValidator
    awg = proposed.awg or 19
    area_espira = pv.total_copper_area_mm2(awg=awg, parallel_count=proposed.paralelos)
    area_limite = area_espira * 1.15 if area_espira else 2.1
    area_total = area_espira * max(1, int(proposed.paralelos or 1) * 36)
    area_total_lim = area_limite * 36

    st.markdown('<div class="dt-insights-panel">', unsafe_allow_html=True)
    st.markdown(
        '<div class="dt-insights-panel__title">Insights Físicos</div>',
        unsafe_allow_html=True,
    )
    render_arc_gauge_row(
        j_val=proposed.j_a_mm2,
        ff_val=proposed.ff,
        b_val=proposed.b_tesla,
    )
    b_status = "warn" if (proposed.b_tesla or 0) > pv.LIMITE_B else "ok"
    render_metric_bar(
        "Área de Cobre — Espira",
        area_espira,
        area_limite,
        unit=" mm²",
        status="ok",
    )
    render_metric_bar(
        "Área de Cobre — Total",
        area_total,
        area_total_lim,
        unit=" mm²",
        status="ok",
    )
    render_metric_bar(
        "Saturação Magnética — Dente",
        proposed.b_tesla,
        1.8,
        unit=" T",
        status=b_status,
    )
    render_insight_kpi_row()
    st.markdown("</div>", unsafe_allow_html=True)


def render_material_inventory(
    proposed: WindingSnapshot,
    entrada: dict[str, Any],
) -> list[dict[str, str]]:
    if not proposed.espiras or not proposed.awg:
        return []
    ran = int(entrada.get("ranhuras") or 36)
    est = estimate_copper_from_winding(
        espiras=float(proposed.espiras),
        awg=float(proposed.awg),
        ranhuras=ran,
        diametro_estator_mm=float(entrada.get("diametro_mm") or 80),
        pacote_mm=float(entrada.get("pacote_mm") or 70),
        parallel_count=proposed.paralelos,
        ligacao=str(entrada.get("ligacao") or ""),
    )
    rows = [
        est.as_table_row(),
        {
            "Item": "Comprimento total estimado",
            "Especificação": f"~{est.comprimento_total_m:.1f} m de condutor",
            "Quantidade": f"{est.peso_kg:.2f} kg Cu",
        },
    ]
    render_material_card(rows, est.peso_kg)
    return rows


def render_diagnostic_suite(
    *,
    entrada: dict[str, Any],
    opt_data: Optional[dict[str, Any]],
    twin_data: Optional[dict[str, Any]],
    res: Optional[dict[str, Any]],
    show_pdf_button: bool = True,
) -> None:
    """Painel completo: comparativo, gauges, material, laudo PDF."""
    proposed = resolve_proposed_snapshot(
        entrada=entrada, opt_data=opt_data, twin_data=twin_data, res=res
    )
    if proposed is None:
        return

    original = resolve_original_snapshot(entrada, twin_data)
    verdict = build_physics_verdict(original, proposed)

    st.markdown('<div class="dt-diagnostics-shell">', unsafe_allow_html=True)
    render_status_chip(verdict.aprovado, verdict.diagnostico)

    render_section_header("Comparativo antes / depois", "Original (sucata) vs proposta de rebobinagem")
    render_comparative_side_by_side(original, proposed)

    render_physics_insights_panel(proposed)

    render_section_header("Inventário de material", "Estimativa geométrica · ρ cobre 8,96 g/cm³")
    render_material_inventory(proposed, entrada)

    if show_pdf_button:
        from services.laudo_rebobinagem_pdf import build_laudo_pdf_bytes

        motor_label = (
            f"Ø{entrada.get('diametro_mm', '—')}×{entrada.get('pacote_mm', '—')} mm · "
            f"{entrada.get('carcaca', '—')} · {entrada.get('ranhuras', '—')} ranhuras"
        )
        c_pdf, _ = st.columns([2, 1])
        with c_pdf:
            if st.button(
                "Gerar Laudo PDF",
                use_container_width=True,
                type="primary",
                key="demo_btn_build_laudo_pdf",
            ):
                try:
                    st.session_state["demo_laudo_pdf_bytes"] = build_laudo_pdf_bytes(
                        motor_modelo=motor_label,
                        original=original,
                        proposed=proposed,
                        verdict=verdict,
                        entrada=entrada,
                    )
                except Exception as exc:
                    st.session_state.pop("demo_laudo_pdf_bytes", None)
                    st.error(f"Não foi possível gerar o PDF: {exc}")

            pdf_bytes = st.session_state.get("demo_laudo_pdf_bytes")
            if pdf_bytes:
                st.download_button(
                    "Baixar Laudo PDF",
                    data=pdf_bytes,
                    file_name="laudo-rebobinagem.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="demo_download_laudo_pdf",
                )
    st.markdown("</div>", unsafe_allow_html=True)
