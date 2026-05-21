#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML de pre-visualizacao — relatorio tecnico de pre-calculo (sem persistencia)."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any


def _esc(v: Any) -> str:
    return html.escape("" if v is None else str(v).strip())


def _fmt_num(v: Any, *, suffix: str = "") -> str:
    if v is None or v == "":
        return "—"
    try:
        f = float(v)
        txt = f"{f:.1f}".rstrip("0").rstrip(".")
        return f"{txt}{suffix}"
    except (TypeError, ValueError):
        return _esc(v)


def build_report_html(
    *,
    entrada: dict[str, Any],
    result: dict[str, Any],
    optimizer: dict[str, Any] | None = None,
    emitted_at: str | None = None,
    ref_id: str | None = None,
) -> str:
    """Gera documento A4 para visualizacao/impressao (nao grava em banco)."""
    now = emitted_at or datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    ref = ref_id or datetime.now(timezone.utc).strftime("PRE-%Y%m%d-%H%M%S")

    diam = entrada.get("diametro_mm") or entrada.get("diametro")
    pac = entrada.get("pacote_mm") or entrada.get("pacote")
    carcaca = entrada.get("carcaca") or ""
    passo = entrada.get("passo") or result.get("passo_moda") or ""
    ligacao = entrada.get("ligacao") or ""
    fio_eng = entrada.get("fio_engenheiro") or entrada.get("fio_eng") or ""
    esp_eng = entrada.get("espiras_engenheiro") or entrada.get("esp_eng") or ""

    cen_b = None
    if optimizer and optimizer.get("cenarios"):
        for cen in optimizer["cenarios"]:
            if str(cen.get("cenario_id")) == "B":
                cen_b = cen
                break

    if cen_b:
        esp_sug = cen_b.get("espiras")
        fio_sug = cen_b.get("wire", {}).get("awg") if isinstance(cen_b.get("wire"), dict) else None
        if fio_sug is None:
            fio_txt = cen_b.get("fio_texto") or ""
            if "AWG" in fio_txt:
                m = re.search(r"(\d+(?:\.\d+)?)\s*AWG", fio_txt)
                if m:
                    fio_sug = m.group(1)
        justificativa = (
            cen_b.get("descricao")
            or result.get("justificativa_tecnica")
            or result.get("validation_message")
            or "Calculo proporcional sobre acervo OFICIAL; conferir na bancada antes de bobinar."
        )
    else:
        esp_sug = result.get("sugestao_espira") or result.get("espiras_media_top5")
        fio_sug = result.get("sugestao_fio_awg") or result.get("fio_medio_top5")
        justificativa = (
            result.get("justificativa_tecnica")
            or result.get("validation_message")
            or "Calculo proporcional sobre acervo OFICIAL; conferir na bancada antes de bobinar."
        )

    alerta = result.get("alerta_risco") or ""
    modo = result.get("modo_processamento") or "proporcional"
    gemini = "Sim" if result.get("gemini_usado") else "Nao"
    validacao = result.get("validation_status") or "—"
    passo_exibir = passo or result.get("passo_moda") or "—"

    matches = result.get("top_matches") or []
    ref_rows = ""
    for i, m in enumerate(matches[:3], start=1):
        ref_rows += (
            f"<tr><td>{i}</td>"
            f"<td>{_esc((m.get('arquivo_rel') or '')[:42])}</td>"
            f"<td>{_fmt_num(m.get('diametro_mm'))} × {_fmt_num(m.get('pacote_mm'))} mm</td>"
            f"<td>{_fmt_num(m.get('espiras_historico'))}</td>"
            f"<td class='highlight'>{_fmt_num(m.get('espiras_calculadas'))}</td></tr>"
        )

    alerta_block = ""
    if alerta:
        alerta_block = (
            f'<div class="alert-box"><strong>Atenção:</strong> {_esc(alerta)}</div>'
        )

    refs_section = ""
    if ref_rows:
        refs_section = (
            '<h2 class="section">Referências proporcionais (amostra)</h2>'
            '<table class="data"><thead><tr>'
            "<th>#</th><th>Arquivo</th><th>Ø × pacote</th><th>Esp. hist.</th><th>Esp. calc.</th>"
            f"</tr></thead><tbody>{ref_rows}</tbody></table>"
        )

    cenarios_section = ""
    if optimizer and optimizer.get("cenarios"):
        cen_rows = ""
        for cen in optimizer["cenarios"]:
            cid = _esc(cen.get("cenario_id", ""))
            esp_c = _fmt_num(cen.get("espiras"))
            fio_c = _esc(cen.get("fio_texto") or cen.get("calibre_display") or "—")
            alt_c = _esc(cen.get("fio_alternativa_paralelo") or "")
            alt_cell = f"<br/><span class='sub'>{alt_c}</span>" if alt_c else ""
            j_c = cen.get("current_density_j")
            ff_c = cen.get("fill_factor_ff")
            conf_c = cen.get("physics_confidence") or cen.get("confidence_score")
            cen_rows += (
                f"<tr><td><strong>{cid}</strong></td>"
                f"<td class='highlight'>{esp_c}</td>"
                f"<td>{fio_c}{alt_cell}</td>"
                f"<td>{_fmt_num(j_c)}</td>"
                f"<td>{_fmt_num(ff_c * 100 if ff_c is not None else None, suffix='%')}</td>"
                f"<td>{_fmt_num(cen.get('fator_ocupacao_ranhura'), suffix='%')}</td>"
                f"<td>{_fmt_num(conf_c, suffix='%')}</td></tr>"
            )
        cenarios_section = (
            "<h2 class='section'>Cenários A / B / C (motor de projetos)</h2>"
            "<table class='data'><thead><tr>"
            "<th>Cenário</th><th>Espiras</th><th>Fio</th><th>J (A/mm²)</th>"
            "<th>ff</th><th>Ocupação</th><th>Confiança</th>"
            f"</tr></thead><tbody>{cen_rows}</tbody></table>"
        )

    parts = [
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'/>",
        f"<title>Pré-Cálculo — {_esc(ref)}</title>",
        "<style>",
        "@page { size: A4; margin: 14mm; }",
        "body { font-family: 'Segoe UI', system-ui, sans-serif; font-size: 11pt; color: #1a1a1a;",
        "background: #e8e8e8; margin: 0; padding: 16px; }",
        ".toolbar { max-width: 210mm; margin: 0 auto 12px; text-align: right; }",
        ".toolbar button { padding: 8px 16px; cursor: pointer; border: none;",
        "background: #1e3a5f; color: #fff; border-radius: 4px; }",
        ".sheet { max-width: 210mm; min-height: 277mm; margin: 0 auto; background: #fff;",
        "padding: 18mm 16mm; box-shadow: 0 2px 12px rgba(0,0,0,.12); }",
        ".brand { display: flex; justify-content: space-between; border-bottom: 2px solid #1e3a5f;",
        "padding-bottom: 10px; margin-bottom: 14px; }",
        ".brand h1 { font-size: 14pt; margin: 0; color: #1e3a5f; }",
        ".sub { font-size: 9pt; color: #555; margin-top: 4px; }",
        ".meta { text-align: right; font-size: 9pt; color: #444; line-height: 1.5; }",
        "h2.section { font-size: 10pt; text-transform: uppercase; color: #1e3a5f;",
        "margin: 18px 0 8px; border-left: 3px solid #1e3a5f; padding-left: 8px; }",
        "table.data { width: 100%; border-collapse: collapse; font-size: 10pt; }",
        "table.data th, table.data td { border: 1px solid #ccc; padding: 7px 10px; }",
        "table.data th { background: #f4f6f8; width: 32%; }",
        "table.data td.highlight { font-weight: 700; color: #1e3a5f; }",
        ".sugestao-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }",
        ".sugestao-card { border: 1px solid #1e3a5f; padding: 12px; text-align: center; }",
        ".sugestao-card .val { font-size: 22pt; font-weight: 700; color: #1e3a5f; }",
        ".sugestao-card .lbl { font-size: 8pt; text-transform: uppercase; color: #666; }",
        ".nota { border: 1px solid #ddd; background: #fafbfc; padding: 12px; line-height: 1.55; }",
        ".alert-box { border: 1px solid #c9a227; background: #fff9e6; padding: 10px; margin-top: 10px; }",
        ".footer-legal { margin-top: 24px; padding-top: 12px; border-top: 1px dashed #999;",
        "font-size: 8.5pt; color: #555; text-align: center; line-height: 1.5; }",
        ".badge { font-size: 8pt; padding: 2px 8px; background: #eef2f7; color: #1e3a5f;",
        "border-radius: 3px; margin-right: 4px; }",
        "@media print { body { background: #fff; padding: 0; } .toolbar { display: none; } .sheet { box-shadow: none; } }",
        "</style></head><body>",
        "<div class='toolbar'><button type='button' onclick='window.print()'>Imprimir / Salvar PDF</button></div>",
        "<article class='sheet'>",
        "<header class='brand'><div>",
        "<h1>Ordem de Serviço: Pré-Cálculo de Rebobinagem</h1>",
        "<div class='sub'>MOTO-RENEW — Relatório de engenharia (somente visualização)</div>",
        "</div><div class='meta'>",
        f"<div><strong>Ref.:</strong> {_esc(ref)}</div>",
        f"<div><strong>Emitido:</strong> {_esc(now)}</div>",
        "<div><span class='badge'>PRÉ-CÁLCULO</span><span class='badge'>NÃO OFICIAL</span></div>",
        "</div></header>",
        "<h2 class='section'>Dados do motor (entrada)</h2>",
        "<table class='data'>",
        f"<tr><th>Diâmetro estator</th><td>{_fmt_num(diam, suffix=' mm')}</td></tr>",
        f"<tr><th>Comprimento pacote</th><td>{_fmt_num(pac, suffix=' mm')}</td></tr>",
        f"<tr><th>Carcaça NEMA/IEC</th><td>{_esc(carcaca) or '—'}</td></tr>",
        f"<tr><th>Passos bobinagem</th><td>{_esc(passo) or '—'}</td></tr>",
        f"<tr><th>Tipo de ligação</th><td>{_esc(ligacao) or '—'}</td></tr>",
        f"<tr><th>Fio / espiras (referência)</th><td>{_esc(fio_eng) or '—'} AWG · {_esc(esp_eng) or '—'} esp.</td></tr>",
        "</table>",
        "<h2 class='section'>Sugestão técnica (sistema)</h2>",
        "<div class='sugestao-grid'>",
        f"<div class='sugestao-card'><div class='val'>{_fmt_num(esp_sug)}</div><div class='lbl'>Espiras</div></div>",
        f"<div class='sugestao-card'><div class='val'>{_fmt_num(fio_sug)}</div><div class='lbl'>Fio AWG</div></div>",
        f"<div class='sugestao-card'><div class='val'>{_esc(passo_exibir)}</div><div class='lbl'>Passo / bobina</div></div>",
        "</div>",
        "<table class='data' style='margin-top:10px'>",
        f"<tr><th>Ligação</th><td>{_esc(ligacao) or '—'}</td></tr>",
        f"<tr><th>Média proporcional</th><td>{_fmt_num(result.get('espiras_media_top5'))} espiras</td></tr>",
        f"<tr><th>Processamento</th><td>{_esc(modo)} · Gemini: {_esc(gemini)} · Validação: {_esc(validacao)}</td></tr>",
        "</table>",
        cenarios_section,
        "<h2 class='section'>Nota de engenharia</h2>",
        f"<div class='nota'>{_esc(justificativa)}</div>",
        alerta_block,
        refs_section,
        "<footer class='footer-legal'>",
        "<strong>Relatório de pré-cálculo. Não oficial. Sujeito à conferência física do rebobinador.</strong><br/>",
        "Apenas visualização — não grava cadastro, manifesto nem banco de dados.<br/>",
        "Confira passo, ligação (estrela/triângulo) e isolamento no motor real antes de bobinar.",
        "</footer></article></body></html>",
    ]
    html_out = "".join(parts)
    return html_out.replace("<div", "<div").replace("</div>", "</div>")
