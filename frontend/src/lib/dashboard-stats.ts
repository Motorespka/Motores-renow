/**
 * Métricas da Visão geral alinhadas a `page/visao_geral.py` (Streamlit).
 */

export function parseRowDate(value: unknown): Date | null {
  const txt = String(value ?? "").trim();
  if (!txt) return null;
  const d = new Date(txt.length >= 19 ? txt.slice(0, 19) : txt);
  if (Number.isNaN(d.getTime())) return null;
  return d;
}

export function countRecentSince(rows: Record<string, unknown>[], days: number): number {
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  let c = 0;
  for (const r of rows) {
    const d =
      parseRowDate(r.created_at) ??
      parseRowDate(r.updated_at) ??
      parseRowDate(r.CreatedAt) ??
      parseRowDate(r.UpdatedAt);
    if (d && d.getTime() >= cutoff) c++;
  }
  return c;
}

export function isNonEmptyDict(v: unknown): boolean {
  return !!(v && typeof v === "object" && !Array.isArray(v) && Object.keys(v as object).length > 0);
}

/** Igual ideia ao `_count_ocr` do Streamlit: JSON de IA ou ficha técnica preenchida. */
export function countOcrOrStructured(rows: Record<string, unknown>[]): number {
  let c = 0;
  for (const r of rows) {
    if (isNonEmptyDict(r.leitura_gemini_json)) {
      c++;
      continue;
    }
    if (isNonEmptyDict(r.dados_tecnicos_json)) {
      c++;
      continue;
    }
  }
  return c;
}

export function countObservacoesRevisao(rows: Record<string, unknown>[]): number {
  return rows.filter((r) => {
    const o = String(r.observacoes ?? r.Observacoes ?? "").toLowerCase();
    return o.includes("inconsist") || o.includes("revis");
  }).length;
}

export type StageInfo = { label: string; variant: "primary" | "accent" | "warning"; pct: number };

export function rowStage(row: Record<string, unknown>): StageInfo {
  const hasPayload =
    isNonEmptyDict(row.leitura_gemini_json) || isNonEmptyDict(row.dados_tecnicos_json);
  const o = String(row.observacoes ?? row.Observacoes ?? "").toLowerCase();
  if (o.includes("inconsist") || o.includes("revis")) {
    return { label: "REVISÃO", variant: "warning", pct: 80 };
  }
  if (hasPayload) {
    return { label: "EM ANÁLISE", variant: "primary", pct: 60 };
  }
  return { label: "PENDENTE", variant: "accent", pct: 15 };
}

export function etaLabel(row: Record<string, unknown>): string {
  const d =
    parseRowDate(row.created_at) ??
    parseRowDate(row.updated_at) ??
    parseRowDate(row.CreatedAt) ??
    parseRowDate(row.UpdatedAt);
  if (!d) return "—";
  const ageH = (Date.now() - d.getTime()) / 3600000;
  if (ageH < 20) return "Hoje";
  if (ageH < 48) return "Amanhã";
  return "2+ dias";
}

export function pickMotorTitleFromRow(row: Record<string, unknown>): string {
  const marca = String(row.marca ?? row.Marca ?? "Motor").trim() || "Motor";
  const modelo = String(row.modelo ?? row.Modelo ?? row.modelo_iec ?? row.modelo_nema ?? "").trim();
  if (modelo) return `${marca} — ${modelo}`;
  return marca;
}

export type OriginBreakdown = { ocr: number; manual: number; historico: number; inferido: number };

/**
 * Distribuição heurística (UI "Origem dos dados") — espelha categorias do Streamlit:
 * OCR / Manual / Histórico / Inferido.
 */
export function inferOriginBreakdown(rows: Record<string, unknown>[]): OriginBreakdown {
  const out: OriginBreakdown = { ocr: 0, manual: 0, historico: 0, inferido: 0 };
  if (!rows.length) return out;
  for (const r of rows) {
    const orig = String(r.origem ?? r.Origem ?? "").toLowerCase();
    const hasGemini = isNonEmptyDict(r.leitura_gemini_json);
    const hasRawText = String(r.texto_bruto_extraido ?? r.TextoBrutoExtraido ?? "").trim().length > 0;
    if (hasGemini || hasRawText) {
      out.ocr++;
      continue;
    }
    if (/import|csv|xlsx|excel|planilha/.test(orig)) {
      out.manual++;
      continue;
    }
    if (isNonEmptyDict(r.dados_tecnicos_json) || String(r.marca ?? r.Marca ?? "").trim()) {
      out.manual++;
      continue;
    }
    if (/hist|legad|antig/.test(orig)) {
      out.historico++;
      continue;
    }
    out.inferido++;
  }
  return out;
}

/** Percentagens inteiras que somam 100 (último ajuste corrige arredondamento). */
export function originPercents(b: OriginBreakdown): [number, number, number, number] {
  const t = b.ocr + b.manual + b.historico + b.inferido;
  if (!t) return [25, 25, 25, 25];
  const keys: (keyof OriginBreakdown)[] = ["ocr", "manual", "historico", "inferido"];
  const raw = keys.map((k) => Math.floor((b[k] / t) * 100));
  const diff = 100 - raw.reduce((a, x) => a + x, 0);
  raw[0] += diff;
  return raw as [number, number, number, number];
}
