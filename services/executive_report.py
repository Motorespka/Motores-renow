#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relatório Analítico Executivo em Markdown + tabelas e Mermaid."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from services.digital_twin_engine import WindingCandidate


def _fmt_j(j: Optional[float]) -> str:
    if j is None:
        return "—"
    return f"{j:.2f}"


def _fmt_ff(ff: float) -> str:
    return f"{ff * 100:.1f}%"


def candidates_table_markdown(candidatos: list[WindingCandidate]) -> str:
    if not candidatos:
        return "_Nenhum candidato gerado._\n"
    lines = [
        "| Opção | Espiras/bobina | Fio (AWG) | Densidade (J) | Ocupação (ff) | Confiança (%) |",
        "|-------|----------------|-----------|---------------|---------------|---------------|",
    ]
    for c in candidatos:
        fio = c.descricao or (f"{c.paralelo}x {c.fio_awg} AWG" if c.paralelo > 1 else f"1x {c.fio_awg} AWG")
        lines.append(
            f"| **{c.opcao}** | {c.espiras_por_bobina:.1f} | {fio} | "
            f"{_fmt_j(c.densidade_j)} A/mm² | {_fmt_ff(c.ocupacao_ff)} | {c.confianca_pct}% |"
        )
    return "\n".join(lines) + "\n"


def build_executive_markdown(
    *,
    modo: str,
    entrada: dict[str, Any],
    candidatos: list[WindingCandidate],
    checklist: Optional[list[str]] = None,
    bloqueado: bool = False,
    visao: Optional[dict[str, Any]] = None,
    gemini: Optional[dict[str, Any]] = None,
    fem_refs: Optional[dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    titulo = (
        "Projeto Caixa Preta (estator vazio)"
        if modo == "caixa_preta"
        else "Auditoria de Cálculo Suspeito"
    )

    parts = [
        f"# Relatório Analítico Executivo — {titulo}",
        f"_Emitido: {now}_\n",
        "## Dados de entrada",
        f"- Ø estator: **{entrada.get('diametro_mm', '—')}** mm",
        f"- Pacote ferro: **{entrada.get('pacote_mm', '—')}** mm",
        f"- Ranhuras: **{entrada.get('ranhuras', '—')}**",
        f"- Polos: **{entrada.get('polos', '—')}**",
        f"- Ligação: **{entrada.get('ligacao', 'Estrela')}**",
        f"- Tensão: **{entrada.get('tensao_rede') or entrada.get('tensao_v') or entrada.get('voltagem') or 220}** V",
    ]

    if fem_refs:
        parts.append("\n## Referências FEM (B ≤ 1,5 T)")
        for k, v in fem_refs.items():
            parts.append(f"- {k}: **{v}**")

    if visao:
        parts.append("\n## Visão computacional")
        conf = visao.get("confianca_visao_0_100", "—")
        parts.append(f"- Confiança visão: **{conf}%**")
        if visao.get("ranhuras_contadas"):
            parts.append(f"- Ranhuras contadas: **{visao['ranhuras_contadas']}**")
        if visao.get("escala_detectada"):
            parts.append(f"- Escala: {visao['escala_detectada']}")
        if visao.get("observacoes"):
            parts.append(f"- _{visao['observacoes']}_")

    if bloqueado and checklist:
        parts.append("\n## ⚠️ Alerta — dados faltantes")
        parts.append(
            "A geração do projeto físico está **travada** até o técnico medir/informar:\n"
        )
        for item in checklist:
            parts.append(f"- [ ] {item}")
        parts.append(
            "\n> Sem tensão, geometria ou ranhuras confirmadas, a FEM e os filtros "
            "de sobrevivência (J, ff) não podem ser aplicados com confiança.\n"
        )
        return "\n".join(parts)

    parts.append("\n## Tabela de candidatos otimizados\n")
    parts.append(candidates_table_markdown(candidatos))

    for c in candidatos:
        if c.alertas:
            parts.append(f"\n**Alertas opção {c.opcao}:** " + "; ".join(c.alertas))

    parts.append("\n## Critérios de confiança")
    parts.append(
        "- **100%** apenas se J ≈ 4 A/mm², ff ≈ 35% e saturação B ≤ 1,5 T respeitada.\n"
        "- **ff > 45%**: cálculo impossível (fio não cabe).\n"
        "- **ff < 25%**: subdimensionado.\n"
        "- **J fora de 3–7 A/mm²**: cálculo invalidado — correção de bitola obrigatória.\n"
    )

    if gemini:
        parts.append("\n## Parecer IA (Gemini)")
        parts.append(f"- Status: **{gemini.get('status_auditoria', gemini.get('validacao_magnetica', '—'))}**")
        com = gemini.get("comentario") or gemini.get("comentario_validacao") or ""
        if com:
            parts.append(f"- {com}")
        if gemini.get("alerta_risco"):
            parts.append(f"- ⚠️ {gemini['alerta_risco']}")

    parts.append("\n## Fluxo de validação física\n")
    parts.append("```mermaid\nflowchart TD\n")
    parts.append("    A[Entrada] --> B{FEM B<=1.5T}\n")
    parts.append("    B --> C[ff 25-45%]\n")
    parts.append("    C --> D[J 3-7 A/mm2]\n")
    parts.append("    D --> E[Score confianca]\n")
    parts.append("```\n")

    return "\n".join(parts)
