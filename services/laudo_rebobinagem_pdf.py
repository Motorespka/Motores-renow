#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Laudo técnico de rebobinagem — PDF (fpdf2).

Selos de aprovação baseados em PhysicsValidatorEngine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any, TYPE_CHECKING

from fpdf.enums import XPos, YPos

from engine.copper_inventory import estimate_copper_from_winding
from engine.physics_validator import PhysicsValidatorEngine
from services.oficina_pdf import _DeliveryPDF, _setup_body_font, _txt

if TYPE_CHECKING:
    from engine.physics_validator import PhysicsValidationVerdict
    from page.demo_calculo_diagnostics import WindingSnapshot


def _conclusao_tecnica(verdict: "PhysicsValidationVerdict") -> str:
    if verdict.aprovado:
        if verdict.elegivel_estrela:
            return (
                "O projeto de rebobinagem encontra-se APROVADO pelos critérios do gêmeo digital "
                "(J, ff e B dentro dos limites WEG/IEC). O fator de enchimento está na zona de "
                "excelência (30–40%), apto ao selo de recomendação técnica."
            )
        return (
            "O projeto encontra-se APROVADO pelos limites obrigatórios de física (J, ff, B). "
            "Recomenda-se conferência na bancada antes de bobinar."
        )
    return (
        f"PROJETO REPROVADO. {verdict.diagnostico} "
        "Não bobinar com esta configuração até corrigir espiras, bitola ou paralelos."
    )


def build_laudo_pdf_bytes(
    *,
    motor_modelo: str,
    original: "WindingSnapshot",
    proposed: "WindingSnapshot",
    verdict: "PhysicsValidationVerdict",
    entrada: dict[str, Any],
) -> bytes:
    ref = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    DeliveryPDF = _DeliveryPDF.build(
        header_line1="MOTO-RENEW — Gêmeo Digital",
        header_line2=f"Laudo de Rebobinagem · {ref}",
        footer_left="Laudo técnico — não substitui ensaio de bancada",
    )
    pdf = DeliveryPDF(orientation="P", unit="mm", format="A4")
    pdf._mr_family, unicode_ok = _setup_body_font(pdf)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    family = pdf._mr_family

    def cell(text: str, h: float = 7, *, bold: bool = False, size: int = 10) -> None:
        pdf.set_font(family, "B" if bold else "", size)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(
            0,
            h,
            _txt(text, unicode_ok),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    pdf.set_fill_color(30, 35, 42)
    y0 = pdf.get_y()
    pdf.rect(pdf.l_margin, y0, 42, 12, style="F")
    pdf.set_xy(pdf.l_margin + 2, y0 + 3)
    pdf.set_font(family, "B", 9)
    pdf.set_text_color(222, 255, 154)
    pdf.cell(38, 5, _txt("MOTO-RENEW", unicode_ok))
    pdf.ln(14)
    pdf.set_text_color(0, 0, 0)

    cell("LAUDO TÉCNICO DE REBOBINAGEM", bold=True, size=16)
    cell(f"Referência: LAUDO-{ref}")
    cell(f"Modelo / estator: {motor_modelo}")
    cell(
        f"Carcaça: {entrada.get('carcaca', '—')} · "
        f"Passo: {entrada.get('passo', '—')} · Ligação: {entrada.get('ligacao', '—')}"
    )
    pdf.ln(2)

    cell("Comparativo Original vs. Projetado", bold=True, size=12)

    def row(label: str, orig: str, prop: str) -> None:
        cell(f"{label}: Original = {orig} | Projetado = {prop}")

    row("Espiras", str(original.espiras or "—"), str(proposed.espiras or "—"))
    row("Bitola", original.fio_texto, proposed.fio_texto)
    j_o = f"{original.j_a_mm2:.2f}" if original.j_a_mm2 is not None else "—"
    j_p = f"{proposed.j_a_mm2:.2f}" if proposed.j_a_mm2 is not None else "—"
    row("J (A/mm²)", j_o, j_p)
    ff_o = f"{(original.ff or 0) * 100:.1f}%" if original.ff is not None else "—"
    ff_p = f"{(proposed.ff or 0) * 100:.1f}%" if proposed.ff is not None else "—"
    row("ff", ff_o, ff_p)
    b_o = f"{original.b_tesla:.2f} T" if original.b_tesla is not None else "—"
    b_p = f"{proposed.b_tesla:.2f} T" if proposed.b_tesla is not None else "—"
    row("B (Tesla est.)", b_o, b_p)

    pdf.ln(2)
    cell("Selo de validação física (PhysicsValidator)", bold=True, size=12)
    selo = "APROVADO" if verdict.aprovado else "REPROVADO"
    if verdict.aprovado:
        pdf.set_text_color(63, 185, 80)
    else:
        pdf.set_text_color(248, 81, 73)
    cell(f">>> {selo} <<<", bold=True, size=14)
    pdf.set_text_color(0, 0, 0)
    for line in PhysicsValidatorEngine.format_output_block(verdict).split("\n"):
        if line.strip():
            cell(line.strip())

    cell("Conclusão técnica", bold=True, size=12)
    cell(_conclusao_tecnica(verdict))

    if proposed.espiras and proposed.awg:
        ran = int(entrada.get("ranhuras") or 36)
        est = estimate_copper_from_winding(
            espiras=float(proposed.espiras),
            awg=float(proposed.awg),
            ranhuras=ran,
            diametro_estator_mm=float(entrada.get("diametro_mm") or 80),
            pacote_mm=float(entrada.get("pacote_mm") or 70),
            parallel_count=proposed.paralelos,
        )
        cell("Material estimado", bold=True, size=12)
        cell(f"Cobre necessário (estimativa): {est.peso_kg:.2f} kg")

    cell(
        "Documento gerado automaticamente pelo Gêmeo Digital. "
        "Não substitui ensaio de bancada ou norma de fabricante.",
        size=8,
    )

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()
