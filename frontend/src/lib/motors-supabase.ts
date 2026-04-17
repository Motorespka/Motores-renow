import { isDefaultLocalApiBase } from "./api";
import { supabase, SUPABASE_CONFIGURED } from "./supabase";
import type { MotorDetailResponse, MotorListResponse, MotorRecord } from "./types";

/** Vercel sem FastAPI: lista/detalhe vêm do Supabase com o JWT do usuário (RLS aplicada). */
export function shouldFetchMotorsFromSupabase(): boolean {
  return SUPABASE_CONFIGURED && isDefaultLocalApiBase();
}

function sanitizeSearch(term: string): string {
  return term.replace(/[^\p{L}\p{N}\s.\-]/gu, "").slice(0, 80).trim();
}

function rowToMotorRecord(row: Record<string, unknown>): MotorRecord {
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
    potencia: String(row.potencia ?? row.Potencia ?? "-"),
    rpm: String(row.rpm ?? row.Rpm ?? row.RPM ?? "-")
  };
}

function rowMatchesSearch(row: Record<string, unknown>, s: string): boolean {
  if (!s) return true;
  const low = s.toLowerCase();
  const blob = [row.marca, row.modelo, row.modelo_iec, row.modelo_nema, row.potencia, row.rpm]
    .map((x) => String(x ?? "").toLowerCase())
    .join(" ");
  return blob.includes(low);
}

async function selectMotoresOrdered(table: string, fetchLimit: number) {
  const ordered = await supabase
    .from(table)
    .select("id, marca, modelo, modelo_iec, modelo_nema, potencia, rpm, tensao, created_at")
    .order("created_at", { ascending: false })
    .limit(fetchLimit);
  if (!ordered.error) return ordered;
  return supabase
    .from(table)
    .select("id, marca, modelo, modelo_iec, modelo_nema, potencia, rpm, tensao, created_at")
    .limit(fetchLimit);
}

export async function fetchMotorListFromSupabase(q: string, limit: number): Promise<MotorListResponse | null> {
  if (!shouldFetchMotorsFromSupabase()) return null;

  const lim = Math.min(Math.max(limit, 1), 100);
  const s = sanitizeSearch(q);
  const fetchLimit = s ? Math.min(500, Math.max(lim * 25, 120)) : lim;

  let { data, error } = await selectMotoresOrdered("motores", fetchLimit);
  if (error) {
    const second = await selectMotoresOrdered("vw_consulta_motores", fetchLimit);
    data = second.data;
    error = second.error;
  }

  if (error || !data) {
    return { mode: "full", total: 0, items: [] };
  }

  let rows = (data as Record<string, unknown>[]).filter((r) => rowMatchesSearch(r, s));
  rows = rows.slice(0, lim);

  const items = rows.map((r) => rowToMotorRecord(r));
  return { mode: "full", total: items.length, items };
}

export async function fetchMotorDetailFromSupabase(motorId: string): Promise<MotorDetailResponse | null> {
  if (!shouldFetchMotorsFromSupabase()) return null;

  const { data, error } = await supabase.from("motores").select("*").eq("id", motorId).maybeSingle();
  if (!error && data) {
    const raw = data as Record<string, unknown>;
    return { item: rowToMotorRecord(raw), raw };
  }

  const v = await supabase.from("vw_consulta_motores").select("*").eq("id", motorId).maybeSingle();
  if (!v.error && v.data) {
    const raw = v.data as Record<string, unknown>;
    return { item: rowToMotorRecord(raw), raw };
  }

  return null;
}
