"use client";

import { FileText, Printer, X } from "lucide-react";
import { useMemo, useRef } from "react";

type Entrada = {
  diametro_mm?: number | string;
  pacote_mm?: number | string;
  carcaca?: string;
  passo?: string;
  ligacao?: string;
  fio_engenheiro?: string;
  espiras_engenheiro?: string;
};

type Result = {
  sugestao_espira?: number | null;
  sugestao_fio_awg?: number | null;
  espiras_media_top5?: number | null;
  fio_medio_top5?: number | null;
  passo_moda?: string;
  justificativa_tecnica?: string;
  alerta_risco?: string;
  modo_processamento?: string;
  gemini_usado?: boolean;
  validation_status?: string;
  top_matches?: Array<{
    arquivo_rel?: string;
    diametro_mm?: number;
    pacote_mm?: number;
    espiras_historico?: number;
    espiras_calculadas?: number;
  }>;
};

function esc(v: unknown): string {
  if (v == null) return "";
  return String(v)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmtNum(v: unknown, suffix = ""): string {
  if (v == null || v === "") return "—";
  const n = Number(v);
  if (Number.isNaN(n)) return esc(v);
  const txt = n % 1 === 0 ? String(n) : n.toFixed(1).replace(/\.0$/, "");
  return `${txt}${suffix}`;
}

export function buildReportHtml(entrada: Entrada, result: Result): string {
  const ref = `PRE-${new Date().toISOString().slice(0, 19).replace(/[-:T]/g, "").slice(0, 13)}`;
  const now = new Date().toLocaleString("pt-BR", { timeZone: "UTC" }) + " UTC";
  const passo = entrada.passo || result.passo_moda || "—";
  const esp = result.sugestao_espira ?? result.espiras_media_top5;
  const fio = result.sugestao_fio_awg ?? result.fio_medio_top5;
  const justificativa =
    result.justificativa_tecnica ||
    "Cálculo proporcional sobre acervo OFICIAL; conferir na bancada antes de bobinar.";

  const refRows = (result.top_matches || [])
    .slice(0, 3)
    .map(
      (m, i) =>
        `<tr><td>${i + 1}</td><td>${esc((m.arquivo_rel || "").slice(0, 42))}</td>` +
        `<td>${fmtNum(m.diametro_mm)} × ${fmtNum(m.pacote_mm)} mm</td>` +
        `<td>${fmtNum(m.espiras_historico)}</td>` +
        `<td class="highlight">${fmtNum(m.espiras_calculadas)}</td></tr>`
    )
    .join("");

  const alerta = result.alerta_risco
    ? `<div class="alert-box"><strong>Atenção:</strong> ${esc(result.alerta_risco)}</div>`
    : "";

  const refs = refRows
    ? `<h2 class="section">Referências proporcionais (amostra)</h2><table class="data"><thead><tr><th>#</th><th>Arquivo</th><th>Ø × pacote</th><th>Esp. hist.</th><th>Esp. calc.</th></tr></thead><tbody>${refRows}</tbody></table>`
    : "";

  return `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"/><title>Pré-Cálculo — ${esc(ref)}</title>
<style>
@page{size:A4;margin:14mm}body{font-family:"Segoe UI",system-ui,sans-serif;font-size:11pt;color:#1a1a1a;background:#e8e8e8;margin:0;padding:16px}
.toolbar{max-width:210mm;margin:0 auto 12px;text-align:right}.toolbar button{padding:8px 16px;background:#1e3a5f;color:#fff;border:none;border-radius:4px;cursor:pointer}
.sheet{max-width:210mm;min-height:277mm;margin:0 auto;background:#fff;padding:18mm 16mm;box-shadow:0 2px 12px rgba(0,0,0,.12)}
.brand{display:flex;justify-content:space-between;border-bottom:2px solid #1e3a5f;padding-bottom:10px;margin-bottom:14px}
.brand h1{font-size:14pt;margin:0;color:#1e3a5f}.sub{font-size:9pt;color:#555;margin-top:4px}.meta{text-align:right;font-size:9pt;color:#444;line-height:1.5}
h2.section{font-size:10pt;text-transform:uppercase;color:#1e3a5f;margin:18px 0 8px;border-left:3px solid #1e3a5f;padding-left:8px}
table.data{width:100%;border-collapse:collapse;font-size:10pt}table.data th,table.data td{border:1px solid #ccc;padding:7px 10px}
table.data th{background:#f4f6f8;width:32%}table.data td.highlight{font-weight:700;color:#1e3a5f}
.sugestao-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}.sugestao-card{border:1px solid #1e3a5f;padding:12px;text-align:center}
.sugestao-card .val{font-size:22pt;font-weight:700;color:#1e3a5f}.sugestao-card .lbl{font-size:8pt;text-transform:uppercase;color:#666}
.nota{border:1px solid #ddd;background:#fafbfc;padding:12px;line-height:1.55}.alert-box{border:1px solid #c9a227;background:#fff9e6;padding:10px;margin-top:10px}
.footer-legal{margin-top:24px;padding-top:12px;border-top:1px dashed #999;font-size:8.5pt;color:#555;text-align:center;line-height:1.5}
.badge{font-size:8pt;padding:2px 8px;background:#eef2f7;color:#1e3a5f;border-radius:3px;margin-right:4px}
@media print{body{background:#fff;padding:0}.toolbar{display:none}.sheet{box-shadow:none}}
</style></head><body>
<div class="toolbar"><button type="button" onclick="window.print()">Imprimir / Salvar PDF</button></div>
<article class="sheet"><header class="brand"><div><h1>Ordem de Serviço: Pré-Cálculo de Rebobinagem</h1>
<div class="sub">MOTO-RENEW — Relatório de engenharia (somente visualização)</div></motion>
<div class="meta"><div><strong>Ref.:</strong> ${esc(ref)}</div><div><strong>Emitido:</strong> ${esc(now)}</div>
<div><span class="badge">PRÉ-CÁLCULO</span><span class="badge">NÃO OFICIAL</span></div></div></header>
<h2 class="section">Dados do motor (entrada)</h2><table class="data">
<tr><th>Diâmetro estator</th><td>${fmtNum(entrada.diametro_mm, " mm")}</td></tr>
<tr><th>Comprimento pacote</th><td>${fmtNum(entrada.pacote_mm, " mm")}</td></tr>
<tr><th>Carcaça NEMA/IEC</th><td>${esc(entrada.carcaca) || "—"}</td></tr>
<tr><th>Passos bobinagem</th><td>${esc(entrada.passo) || "—"}</td></tr>
<tr><th>Tipo de ligação</th><td>${esc(entrada.ligacao) || "—"}</td></tr>
<tr><th>Fio / espiras (referência)</th><td>${esc(entrada.fio_engenheiro) || "—"} AWG · ${esc(entrada.espiras_engenheiro) || "—"} esp.</td></tr></table>
<h2 class="section">Sugestão técnica (sistema)</h2><div class="sugestao-grid">
<div class="sugestao-card"><div class="val">${fmtNum(esp)}</div><div class="lbl">Espiras</div></div>
<div class="sugestao-card"><div class="val">${fmtNum(fio)}</motion><div class="lbl">Fio AWG</div></div>
<div class="sugestao-card"><div class="val">${esc(passo)}</div><div class="lbl">Passo / bobina</div></div></div>
<table class="data" style="margin-top:10px"><tr><th>Ligação</th><td>${esc(entrada.ligacao) || "—"}</td></tr>
<tr><th>Média proporcional</th><td>${fmtNum(result.espiras_media_top5)} espiras</td></tr>
<tr><th>Processamento</th><td>${esc(result.modo_processamento)} · Gemini: ${result.gemini_usado ? "Sim" : "Não"} · Validação: ${esc(result.validation_status)}</td></tr></table>
<h2 class="section">Nota de engenharia</h2><div class="nota">${esc(justificativa)}</div>${alerta}${refs}
<footer class="footer-legal"><strong>Relatório de pré-cálculo. Não oficial. Sujeito à conferência física do rebobinador.</strong><br/>
Apenas visualização — não grava cadastro, manifesto nem banco de dados.<br/>
Confira passo, ligação (estrela/triângulo) e isolamento no motor real antes de bobinar.</footer></article></body></html>`
    .replace(/<div/g, "<div")
    .replace(/<\/motion>/g, "</div>");
}

type Props = {
  open: boolean;
  onClose: () => void;
  entrada: Entrada;
  result: Result;
};

export function DemoCalculoReportModal({ open, onClose, entrada, result }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const html = useMemo(() => buildReportHtml(entrada, result), [entrada, result]);

  if (!open) return null;

  function downloadHtml() {
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `previa-rebobinagem-${Date.now()}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function printReport() {
    iframeRef.current?.contentWindow?.print();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-4xl max-h-[95vh] flex flex-col rounded-xl border border-border/60 bg-card shadow-2xl">
        <div className="flex items-center justify-between gap-3 p-4 border-b border-border/40">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            <div>
              <div className="font-display text-sm tracking-wider">PRÉVIA DO RELATÓRIO</div>
              <div className="text-[10px] text-muted-foreground">Somente visualização — não grava no banco</div>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={printReport}
              className="h-9 px-3 rounded-lg border border-border/50 text-[11px] flex items-center gap-1"
            >
              <Printer className="w-3.5 h-3.5" />
              Imprimir
            </button>
            <button
              type="button"
              onClick={downloadHtml}
              className="h-9 px-3 rounded-lg border border-primary/40 bg-primary/10 text-primary text-[11px]"
            >
              Baixar HTML
            </button>
            <button type="button" onClick={onClose} className="h-9 w-9 rounded-lg border border-border/50 flex items-center justify-center">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
        <iframe
          ref={iframeRef}
          title="Relatório pré-cálculo"
          srcDoc={html}
          className="flex-1 w-full min-h-[70vh] bg-[#e8e8e8] rounded-b-xl"
          sandbox="allow-same-origin allow-scripts allow-modals"
        />
      </div>
    </div>
  );
}
