import { isDefaultLocalApiBase } from "./api";
import { normalizeMotorRowForUi } from "./motor-normalizer";
import { supabase, SUPABASE_CONFIGURED } from "./supabase";
import type { MotorDetailResponse, MotorListResponse, MotorRecord } from "./types";

/** Vercel sem FastAPI: lista/detalhe vêm do Supabase com o JWT do usuário (RLS aplicada). */
export function shouldFetchMotorsFromSupabase(): boolean {
  return SUPABASE_CONFIGURED && isDefaultLocalApiBase();
}

function sanitizeSearch(term: string): string {
  return term.replace(/[^\p{L}\p{N}\s.\-]/gu, "").slice(0, 80).trim();
}

/** Mesma prioridade que o Streamlit: consulta → primary → fallbacks. */
function resolveMotorTableChain(): string[] {
  const consulta = (process.env.NEXT_PUBLIC_SUPABASE_CONSULTA_TABLE || "").trim().toLowerCase();
  const primary = (process.env.NEXT_PUBLIC_SUPABASE_PRIMARY_TABLE || "motores").trim().toLowerCase();
  const legacy = (process.env.NEXT_PUBLIC_MOTORES_SOURCE_TABLE || "").trim().toLowerCase();
  const known = new Set(["motores", "vw_consulta_motores", "vw_motores_para_site", "arquivos_motor"]);
  const out: string[] = [];
  const add = (t: string) => {
    const n = t.trim().toLowerCase();
    if (!n || out.includes(n)) return;
    out.push(n);
  };
  if (consulta) add(consulta);
  else if (legacy && known.has(legacy)) add(legacy);
  else add("vw_motores_para_site");
  add(primary);
  for (const t of ["motores", "vw_motores_para_site", "vw_consulta_motores"]) add(t);
  return out;
}

function idColumnForTable(table: string): "id" | "Id" {
  return table.trim().toLowerCase() === "vw_motores_para_site" ? "Id" : "id";
}

function rowToMotorRecord(row: Record<string, unknown>): MotorRecord {
  const ui = normalizeMotorRowForUi(row);
  const modelo =
    row.modelo ??
    row.Modelo ??
    row.modelo_iec ??
    row.modelo_nema ??
    "-";
  return {
    id: (row.id ?? row.Id) as string | number | undefined,
    marca: String(row.marca ?? row.Marca ?? "Motor"),
    modelo: String(modelo),
    potencia: String(row.potencia ?? row.Potencia ?? ui.potencia ?? "-"),
    rpm: String(row.rpm ?? row.Rpm ?? row.RPM ?? ui.rpm ?? "-"),
    tensao: String(row.tensao ?? row.Tensao ?? ui.tensao ?? ""),
    corrente: String(row.corrente ?? row.Corrente ?? ui.corrente ?? ""),
    polos: String(row.polos ?? row.Polos ?? ui.polos ?? ""),
    frequencia: String(ui.frequencia ?? ""),
    passo_principal: ui.passo_principal,
    espiras_principal: ui.espiras_principal,
    fio_principal: ui.fio_principal,
    eixo: ui.eixo,
    medidas: ui.medidas,
  };
}

function rowMatchesSearch(row: Record<string, unknown>, s: string): boolean {
  if (!s) return true;
  const low = s.toLowerCase();
  const ui = normalizeMotorRowForUi(row);
  const blob = [
    row.marca,
    row.Marca,
    row.modelo,
    row.Modelo,
    row.modelo_iec,
    row.modelo_nema,
    row.potencia,
    row.Potencia,
    row.rpm,
    row.Rpm,
    row.RPM,
    row.tensao,
    row.Tensao,
    row.corrente,
    row.Corrente,
    row.polos,
    row.Polos,
    ui.potencia,
    ui.rpm,
    ui.tensao,
    ui.corrente,
    ui.passo_principal,
    ui.fio_principal,
    ui.tipo_motor,
    ui.medidas,
    ui.eixo,
  ]
    .map((x) => String(x ?? "").toLowerCase())
    .join(" ");
  return blob.includes(low);
}

async function selectMotoresFlexible(table: string, fetchLimit: number) {
  const attempts = [
    () => supabase.from(table).select("*").order("created_at", { ascending: false }).limit(fetchLimit),
    () => supabase.from(table).select("*").order("CreatedAt", { ascending: false }).limit(fetchLimit),
    () => supabase.from(table).select("*").order("updated_at", { ascending: false }).limit(fetchLimit),
    () => supabase.from(table).select("*").order("UpdatedAt", { ascending: false }).limit(fetchLimit),
    () => supabase.from(table).select("*").limit(fetchLimit),
  ];
  for (const run of attempts) {
    const r = await run();
    if (!r.error) return r;
  }
  return await supabase.from(table).select("*").limit(fetchLimit);
}

export async function fetchMotorListFromSupabase(q: string, limit: number): Promise<MotorListResponse | null> {
  if (!shouldFetchMotorsFromSupabase()) return null;

  const lim = Math.min(Math.max(limit, 1), 100);
  const s = sanitizeSearch(q);
  const fetchLimit = s ? Math.min(500, Math.max(lim * 25, 120)) : lim;

  let rows: Record<string, unknown>[] | null = null;
  for (const table of resolveMotorTableChain()) {
    const r = await selectMotoresFlexible(table, fetchLimit);
    if (!r.error && r.data && r.data.length) {
      rows = r.data as Record<string, unknown>[];
      break;
    }
  }

  if (!rows) {
    return { mode: "full", total: 0, items: [] };
  }

  let filtered = rows.filter((r) => rowMatchesSearch(r, s));
  filtered = filtered.slice(0, lim);

  const items = filtered.map((r) => rowToMotorRecord(r));
  return { mode: "full", total: items.length, items };
}

export async function fetchMotorDetailFromSupabase(motorId: string): Promise<MotorDetailResponse | null> {
  if (!shouldFetchMotorsFromSupabase()) return null;

  for (const table of resolveMotorTableChain()) {
    const idCol = idColumnForTable(table);
    const { data, error } = await supabase.from(table).select("*").eq(idCol, motorId).maybeSingle();
    if (!error && data) {
      const raw = data as Record<string, unknown>;
      return { item: rowToMotorRecord(raw), raw };
    }
  }

  return null;
}
