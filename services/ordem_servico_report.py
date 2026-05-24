#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ordem de Serviço — HTML para impressão / Ctrl+P → PDF (bancada).
Sem dependências extras; compatível com Streamlit (download .html).
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any, Optional

from engine.physics_audit import MSG_B_ABORT


def _esc(v: Any) -> str:
    return html.escape("" if v is None else str(v).strip())


def _fmt_num(v: Any, *, suffix: str = "", decimals: int = 1) -> str:
    if v is None or v == "":
        return "—"
    try:
        f = float(v)
        txt = f"{f:.{decimals}f}".rstrip("0").rstrip(".")
        return f"{txt}{suffix}"
    except (TypeError, ValueError):
        return _esc(v)


def calculation_ready_for_export(
    twin_data: Optional[dict[str, Any]],
    opt_data: Optional[dict[str, Any]],
    res: Optional[dict[str, Any]],
) -> bool:
    """Botão de OS só aparece após cálculo utilizável na tela."""
    if res and res.get("calculo_abortado"):
        return False
    if opt_data and opt_data.get("cenarios"):
        from page.demo_calculo_ui import projeto_fisicamente_aprovado

        return projeto_fisicamente_aprovado(opt_data)
    if twin_data:
        if twin_data.get("bloqueado"):
            return False
        return bool(twin_data.get("candidatos")) and bool(twin_data.get("completo"))
    if res:
        if str(res.get("validation_status") or "").upper() == "INCOMPLETO":
            return False
        return bool(
            res.get("sugestao_espira")
            or res.get("espiras_media_top5")
            or res.get("top_matches")
        )
    return False


def _rows_from_twin(twin_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for c in twin_data.get("candidatos") or []:
        ff = c.get("ocupacao_ff")
        rows.append(
            {
                "opcao": c.get("opcao", ""),
                "espiras": c.get("espiras_por_bobina"),
                "fio": c.get("descricao", ""),
                "j": c.get("densidade_j"),
                "ff_pct": round(float(ff) * 100, 1) if ff is not None else None,
                "confianca": c.get("confianca_pct"),
                "alertas": c.get("alertas") or [],
            }
        )
    return rows


def _rows_from_optimizer(opt_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for cen in opt_data.get("cenarios") or []:
        ff = cen.get("fill_factor_ff")
        rows.append(
            {
                "opcao": cen.get("cenario_id", ""),
                "espiras": cen.get("espiras"),
                "fio": cen.get("fio_texto") or cen.get("calibre_display", ""),
                "j": cen.get("current_density_j"),
                "ff_pct": round(float(ff) * 100, 1) if ff is not None else None,
                "confianca": cen.get("physics_confidence") or cen.get("confidence_score"),
                "alertas": cen.get("alertas") or [],
            }
        )
    return rows


def _rows_from_result(res: dict[str, Any]) -> list[dict[str, Any]]:
    esp = res.get("sugestao_espira") or res.get("espiras_media_top5")
    fio = res.get("sugestao_fio_texto") or res.get("sugestao_fio_awg")
    if esp is None and fio is None:
        return []
    return [
        {
            "opcao": "Sistema",
            "espiras": esp,
            "fio": fio,
            "j": None,
            "ff_pct": None,
            "confianca": None,
            "alertas": [res.get("alerta_risco")] if res.get("alerta_risco") else [],
        }
    ]


def collect_export_rows(
    twin_data: Optional[dict[str, Any]],
    opt_data: Optional[dict[str, Any]],
    res: Optional[dict[str, Any]],
) -> list[dict[str, Any]]:
    if opt_data and opt_data.get("cenarios"):
        from page.demo_calculo_ui import resolve_recommended_optimizer_scenario

        if resolve_recommended_optimizer_scenario(opt_data):
            return _rows_from_optimizer(opt_data)
        return []
    if twin_data and twin_data.get("candidatos"):
        return _rows_from_twin(twin_data)
    if res:
        return _rows_from_result(res)
    return []


def _modo_label(
    twin_data: Optional[dict[str, Any]],
    res: Optional[dict[str, Any]],
) -> str:
    if twin_data:
        if twin_data.get("modo") == "caixa_preta":
            return "Caixa preta (FEM + visão)"
        if twin_data.get("modo") == "auditoria":
            return "Auditoria de cálculo"
        return str(twin_data.get("modo") or "Gêmeo digital")
    return str(res.get("modo_processamento") if res else "Acervo proporcional")


def _primary_confidence(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    scores = [int(r.get("confianca") or 0) for r in rows]
    return max(scores) if scores else 0


def build_ordem_servico_html(
    *,
    entrada: dict[str, Any],
    twin_data: Optional[dict[str, Any]] = None,
    opt_data: Optional[dict[str, Any]] = None,
    res: Optional[dict[str, Any]] = None,
    emitted_at: Optional[str] = None,
    ref_id: Optional[str] = None,
) -> str:
    """Documento A4 — Ordem de Serviço para impressão."""
    now = emitted_at or datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
    ref = ref_id or datetime.now(timezone.utc).strftime("OS-%Y%m%d-%H%M%S")

    diam = entrada.get("diametro_mm") or entrada.get("diametro")
    pac = entrada.get("pacote_mm") or entrada.get("pacote")
    ran = entrada.get("ranhuras")
    pol = entrada.get("polos")
    tensao = entrada.get("tensao_v") or entrada.get("voltagem") or "220"
    carcaca = entrada.get("carcaca") or ""
    passo = entrada.get("passo") or ""
    ligacao = entrada.get("ligacao") or "Estrela"

    rows = collect_export_rows(twin_data, opt_data, res)
    conf_primary = _primary_confidence(rows)
    modo = _modo_label(twin_data, res)

    alert_global = ""
    if twin_data and twin_data.get("saturacao_abortada"):
        alert_global = MSG_B_ABORT
        if twin_data.get("flux_density_b_t"):
            alert_global += f" (B ≈ {float(twin_data['flux_density_b_t']):.2f} T)"

    cand_rows_html = ""
    for r in rows:
        alerts_txt = "; ".join(str(a) for a in (r.get("alertas") or []) if a)[:120]
        cand_rows_html += (
            "<tr>"
            f"<td><strong>{_esc(r.get('opcao'))}</strong></td>"
            f"<td class='num'>{_fmt_num(r.get('espiras'))}</td>"
            f"<td>{_esc(r.get('fio'))}</td>"
            f"<td class='num'>{_fmt_num(r.get('j'), decimals=2)}</td>"
            f"<td class='num'>{_fmt_num(r.get('ff_pct'), suffix='%')}</td>"
            f"<td class='num'>{_fmt_num(r.get('confianca'), suffix='%')}</td>"
            f"<td class='small'>{_esc(alerts_txt) or '—'}</td>"
            "</tr>"
        )
    if not cand_rows_html:
        cand_rows_html = (
            "<tr><td colspan='7' style='text-align:center;color:#666'>"
            "Nenhum candidato disponível</td></tr>"
        )

    conf_class = "conf-ok"
    if conf_primary < 50:
        conf_class = "conf-bad"
    elif conf_primary < 80:
        conf_class = "conf-warn"

    alert_block = ""
    if alert_global:
        alert_block = (
            f'<div class="alert-severe"><strong>⚠ Atenção:</strong> {_esc(alert_global)}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"/>
<title>Ordem de Serviço — {_esc(ref)}</title>
<style>
@page {{ size: A4; margin: 12mm; }}
* {{ box-sizing: border-box; }}
body {{
  font-family: "Segoe UI", system-ui, sans-serif;
  font-size: 10.5pt;
  color: #1a1a1a;
  margin: 0;
  padding: 12px;
  background: #e5e5e5;
}}
.toolbar {{
  max-width: 210mm;
  margin: 0 auto 10px;
  text-align: right;
}}
.toolbar button {{
  padding: 10px 18px;
  font-size: 11pt;
  cursor: pointer;
  border: none;
  background: #2d5016;
  color: #fff;
  border-radius: 8px;
  font-weight: 600;
}}
.sheet {{
  max-width: 210mm;
  min-height: 277mm;
  margin: 0 auto;
  background: #fff;
  padding: 14mm 12mm;
  box-shadow: 0 2px 10px rgba(0,0,0,.12);
}}
.header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 3px solid #2d5016;
  padding-bottom: 10px;
  margin-bottom: 14px;
}}
.header h1 {{
  margin: 0;
  font-size: 16pt;
  color: #2d5016;
  letter-spacing: 0.02em;
}}
.header .sub {{ font-size: 9pt; color: #555; margin-top: 4px; }}
.meta {{ text-align: right; font-size: 9pt; color: #444; line-height: 1.5; }}
.badge {{
  display: inline-block;
  font-size: 8pt;
  padding: 2px 8px;
  background: #e8f5e0;
  color: #2d5016;
  border-radius: 4px;
  margin-left: 4px;
}}
h2.section {{
  font-size: 9.5pt;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #2d5016;
  margin: 16px 0 8px;
  border-left: 4px solid #9fd64d;
  padding-left: 8px;
}}
table.data {{
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}}
table.data th, table.data td {{
  border: 1px solid #bbb;
  padding: 6px 8px;
  vertical-align: top;
}}
table.data th {{
  background: #f0f4e8;
  color: #2d5016;
  width: 28%;
  text-align: left;
  font-weight: 600;
}}
table.candidates th {{
  background: #2d5016;
  color: #fff;
  font-size: 8.5pt;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
table.candidates td {{ font-size: 10pt; }}
table.candidates tr:nth-child(even) td {{ background: #f9faf7; }}
td.num {{ text-align: center; font-weight: 600; font-family: Consolas, monospace; }}
td.small {{ font-size: 8.5pt; color: #555; }}
.score-box {{
  text-align: center;
  border: 2px solid #2d5016;
  border-radius: 8px;
  padding: 12px;
  margin: 12px 0;
  max-width: 200px;
}}
.score-box .val {{
  font-size: 28pt;
  font-weight: 800;
  font-family: Consolas, monospace;
}}
.score-box.conf-ok .val {{ color: #1a7f37; }}
.score-box.conf-warn .val {{ color: #9a6700; }}
.score-box.conf-bad .val {{ color: #cf222e; }}
.score-box .lbl {{
  font-size: 8pt;
  text-transform: uppercase;
  color: #666;
  margin-top: 4px;
}}
.obs-box {{
  border: 1px dashed #999;
  min-height: 70px;
  margin-top: 8px;
  padding: 8px;
  background: #fafafa;
}}
.sign-row {{
  display: flex;
  gap: 24px;
  margin-top: 28px;
}}
.sign-block {{
  flex: 1;
  border-top: 1px solid #333;
  padding-top: 6px;
  font-size: 9pt;
  color: #444;
}}
.alert-severe {{
  border: 2px solid #cf222e;
  background: #ffebe9;
  color: #82071e;
  padding: 10px;
  margin: 10px 0;
  border-radius: 6px;
}}
.footer {{
  margin-top: 20px;
  font-size: 8pt;
  color: #666;
  text-align: center;
  border-top: 1px dashed #ccc;
  padding-top: 10px;
}}
@media print {{
  body {{ background: #fff; padding: 0; }}
  .toolbar {{ display: none; }}
  .sheet {{ box-shadow: none; max-width: 100%; }}
}}
</style>
</head>
<body>
<div class="toolbar">
  <button type="button" onclick="window.print()">🖨️ Imprimir / Salvar como PDF</button>
</div>
<article class="sheet">
  <header class="header">
    <div>
      <h1>ORDEM DE SERVIÇO — REBOBINAGEM</h1>
      <div class="sub">Gêmeo Digital · MOTO-RENEW · Uso na bancada</div>
    </div>
    <div class="meta">
      <div><strong>OS:</strong> {_esc(ref)}</div>
      <div><strong>Emitida:</strong> {_esc(now)}</div>
      <div><span class="badge">IMPRESSÃO</span><span class="badge">{_esc(modo)}</span></div>
    </div>
  </header>

  {alert_block}

  <h2 class="section">Dados do estator</h2>
  <table class="data">
    <tr><th>Diâmetro interno</th><td>{_fmt_num(diam, suffix=' mm')}</td></tr>
    <tr><th>Comprimento do pacote</th><td>{_fmt_num(pac, suffix=' mm')}</td></tr>
    <tr><th>Nº de ranhuras</th><td>{_esc(ran) or '—'}</td></tr>
    <tr><th>Nº de polos</th><td>{_esc(pol) if pol else '— (inferido)'}</td></tr>
    <tr><th>Tensão de rede</th><td>{_fmt_num(tensao, suffix=' V')}</td></tr>
    <tr><th>Carcaça NEMA/IEC</th><td>{_esc(carcaca) or '—'}</td></tr>
    <tr><th>Passo bobinagem</th><td>{_esc(passo) or '—'}</td></tr>
    <tr><th>Ligação</th><td>{_esc(ligacao)}</td></tr>
  </table>

  <div class="score-box {conf_class}">
    <div class="val">{conf_primary}%</div>
    <div class="lbl">Score de confiança física (principal)</div>
  </div>

  <h2 class="section">Candidatos validados</h2>
  <table class="data candidates">
    <thead>
      <tr>
        <th>Opção</th><th>Espiras</th><th>Fio (AWG)</th>
        <th>J (A/mm²)</th><th>ff</th><th>Confiança</th><th>Observações</th>
      </tr>
    </thead>
    <tbody>{cand_rows_html}</tbody>
  </table>

  <h2 class="section">Observações do técnico</h2>
  <div class="obs-box"></div>

  <div class="sign-row">
    <div class="sign-block">Técnico responsável — nome legível</div>
    <div class="sign-block">Data ___/___/______</div>
    <div class="sign-block">Assinatura</div>
  </div>

  <footer class="footer">
    Documento gerado pelo sistema de cálculo. Conferir fisicamente passo, ligação e isolamento antes de bobinar.<br/>
    Ctrl+P neste arquivo salva como PDF. Referência: {_esc(ref)}.
  </footer>
</article>
</body>
</html>"""
