/**
 * Resolução de URL GLB para holograma 3D — subconjunto alinhado a
 * `utils/motor_hologram_glb.py` / `resolve_model_glb_url` (Streamlit).
 * Variáveis: use `NEXT_PUBLIC_*` no Vercel; nomes sem prefixo aceites só em dev (Next carrega .env.local).
 */

export const DEFAULT_NEMA56_GLB_URL =
  "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/Nema56.glb";

export const DEFAULT_NEMA42_GLB_URL =
  "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/nema%2042%20closed%20(1).glb";

export const DEFAULT_IEC132_GLB_URL =
  "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/269c0156-2633-44cf-9d80-98c14483011c.glb";

function motorBlock(row: Record<string, unknown>): Record<string, unknown> {
  const dt = row.dados_tecnicos_json;
  if (dt && typeof dt === "object" && !Array.isArray(dt)) {
    const d = dt as Record<string, unknown>;
    const m = d.motor ?? d.Motor;
    if (m && typeof m === "object" && !Array.isArray(m)) return m as Record<string, unknown>;
  }
  return {};
}

function mecanicaBlock(row: Record<string, unknown>): Record<string, unknown> {
  const dt = row.dados_tecnicos_json;
  if (dt && typeof dt === "object" && !Array.isArray(dt)) {
    const d = dt as Record<string, unknown>;
    const m = d.mecanica ?? d.Mecanica;
    if (m && typeof m === "object" && !Array.isArray(m)) return m as Record<string, unknown>;
  }
  return {};
}

function pickCarcaca(d: Record<string, unknown>): string {
  const a = d.carcaca ?? d.Carcaca;
  return String(a ?? "");
}

function carcacaBlob(row: Record<string, unknown>): string {
  const motor = motorBlock(row);
  const mec = mecanicaBlock(row);
  const ui = row._consulta_ui;
  const uiObj = typeof ui === "object" && ui && !Array.isArray(ui) ? (ui as Record<string, unknown>) : null;
  const uiCar = uiObj ? pickCarcaca(uiObj) : "";
  const r = row as Record<string, unknown>;
  const parts = [pickCarcaca(r), pickCarcaca(mec), pickCarcaca(motor), uiCar];
  return parts.join(" ");
}

function carcacaFichaUpper(row: Record<string, unknown>): string {
  const motor = motorBlock(row);
  const mec = mecanicaBlock(row);
  const parts: string[] = [carcacaBlob(row)];
  for (const d of [mec, motor]) {
    for (const k of [
      "carcaca",
      "Carcaca",
      "quadro",
      "quadro_nema",
      "nema",
      "nema_frame",
      "frame",
      "envelope",
    ]) {
      const v = d[k];
      if (v != null && String(v).trim()) parts.push(String(v).trim());
    }
  }
  return parts.join(" ").toUpperCase();
}

const _NEMA56_IN_PLATE = new RegExp(
  String.raw`(?<![0-9])56[A-Z]{0,2}(?![A-Z0-9])(?!\.[0-9])`,
  "i",
);

function fichaIec63SemNemaExplicito(plateUpper: string): boolean {
  const u = plateUpper.trim();
  if (!u || /\bNEMA\b/i.test(u)) return false;
  const c = u.replace(/[\s._\-/]+/g, "");
  return c.includes("IEC63");
}

function nema56InPlateString(plateUpper: string): boolean {
  const b = plateUpper.trim();
  if (!b) return false;
  const s = b.trim();
  if (/^56[A-Z]{0,2}\s*$/i.test(s) || /^NEMA\W*56[A-Z]{0,2}\s*$/i.test(s)) return true;
  if (_NEMA56_IN_PLATE.test(b)) return true;
  if (/\bNEMA\W*56(?!-)(?![0-9])(?!\.[0-9])/i.test(b) || /\bNEMA\W*56[A-Z]{1,2}\b/i.test(b)) return true;
  if (/\bQUADRO\W*56[A-Z]{0,2}(?![A-Z0-9])(?!\.[0-9])/i.test(b)) return true;
  if (/\bFRAME\W*56[A-Z]{0,2}(?![A-Z0-9])(?!\.[0-9])/i.test(b)) return true;
  if (
    /\bCARCA\W*56(?!-)(?![0-9]{2,})[A-Z]{0,2}(?![A-Z0-9])(?!\.[0-9])/i.test(b) ||
    /\bCARCA\W*56(?!-)(?![0-9])(?!\.[0-9])/i.test(b)
  ) {
    return true;
  }
  return false;
}

export function nema56SomenteFichaMecanica(row: Record<string, unknown>): boolean {
  const u = carcacaFichaUpper(row);
  if (fichaIec63SemNemaExplicito(u)) return false;
  return nema56InPlateString(u);
}

function modeloIdentificacaoUpper(row: Record<string, unknown>): string {
  const motor = motorBlock(row);
  const bits: string[] = [];
  for (const k of ["modelo", "modelo_nema", "modelo_iec", "Modelo", "ModeloNema"] as const) {
    const v = motor[k];
    if (v != null && String(v).trim()) bits.push(String(v).trim());
  }
  const r = row as Record<string, unknown>;
  for (const k of ["modelo", "Modelo"] as const) {
    const v = r[k];
    if (v != null && String(v).trim()) bits.push(String(v).trim());
  }
  return bits.join(" ").toUpperCase();
}

/** NEMA 42, NEMA-42, NEMA42 (sem espaço entre NEMA e 42). */
export function nema42SomenteFichaMecanica(row: Record<string, unknown>): boolean {
  const s = `${carcacaFichaUpper(row)} ${modeloIdentificacaoUpper(row)}`.trim();
  if (!s) return false;
  return /NEMA(?:\s*[-_]?\s*)?42\b/i.test(s);
}

function pathLooksGlb(u: string): boolean {
  const x = u.toLowerCase();
  return x.includes(".glb") || x.startsWith("data:model/gltf-binary");
}

function readEnv(...names: string[]): string {
  for (const n of names) {
    const v = process.env[n];
    if (v && String(v).trim()) return String(v).trim();
  }
  return "";
}

function truthyEnv(v: string): boolean {
  return ["1", "true", "yes", "on"].includes(v.trim().toLowerCase());
}

function bakedNema56Activo(): boolean {
  const v = readEnv("NEXT_PUBLIC_HOLOGRAM_BAKED_NEMA56_GLB", "HOLOGRAM_BAKED_NEMA56_GLB").trim().toLowerCase();
  if (["0", "false", "no", "off"].includes(v)) return false;
  return true;
}

function motorIdStr(row: Record<string, unknown>): string {
  for (const k of ["id", "Id", "motor_id"] as const) {
    const v = row[k];
    if (v != null && String(v).trim()) return String(v).trim();
  }
  return "";
}

function nema56GlbEfectivo(): string {
  const fromEnv = readEnv("NEXT_PUBLIC_HOLOGRAM_GLB_NEMA56", "HOLOGRAM_GLB_NEMA56");
  if (fromEnv && /^https?:\/\//i.test(fromEnv) && pathLooksGlb(fromEnv)) return fromEnv;
  if (!bakedNema56Activo()) return "";
  const override = readEnv("NEXT_PUBLIC_HOLOGRAM_DEFAULT_NEMA56_GLB_URL", "HOLOGRAM_DEFAULT_NEMA56_GLB_URL");
  if (override && /^https?:\/\//i.test(override) && pathLooksGlb(override)) return override;
  return DEFAULT_NEMA56_GLB_URL;
}

function bakedNema42Activo(): boolean {
  const v = readEnv("NEXT_PUBLIC_HOLOGRAM_BAKED_NEMA42_GLB", "HOLOGRAM_BAKED_NEMA42_GLB").trim().toLowerCase();
  if (["0", "false", "no", "off"].includes(v)) return false;
  return true;
}

function nema42GlbEfectivo(): string {
  const fromEnv = readEnv("NEXT_PUBLIC_HOLOGRAM_GLB_NEMA42", "HOLOGRAM_GLB_NEMA42");
  if (fromEnv && /^https?:\/\//i.test(fromEnv) && pathLooksGlb(fromEnv)) return fromEnv;
  if (!bakedNema42Activo()) return "";
  const override = readEnv("NEXT_PUBLIC_HOLOGRAM_DEFAULT_NEMA42_GLB_URL", "HOLOGRAM_DEFAULT_NEMA42_GLB_URL");
  if (override && /^https?:\/\//i.test(override) && pathLooksGlb(override)) return override;
  return DEFAULT_NEMA42_GLB_URL;
}

function bakedIec132Activo(): boolean {
  const v = readEnv("NEXT_PUBLIC_HOLOGRAM_BAKED_IEC132_GLB", "HOLOGRAM_BAKED_IEC132_GLB").trim().toLowerCase();
  if (["0", "false", "no", "off"].includes(v)) return false;
  return true;
}

function iec132GlbEfectivo(): string {
  const fromEnv = readEnv("NEXT_PUBLIC_HOLOGRAM_GLB_IEC132", "HOLOGRAM_GLB_IEC132");
  if (fromEnv && /^https?:\/\//i.test(fromEnv) && pathLooksGlb(fromEnv)) return fromEnv;
  if (!bakedIec132Activo()) return "";
  const override = readEnv("NEXT_PUBLIC_HOLOGRAM_DEFAULT_IEC132_GLB_URL", "HOLOGRAM_DEFAULT_IEC132_GLB_URL");
  if (override && /^https?:\/\//i.test(override) && pathLooksGlb(override)) return override;
  return DEFAULT_IEC132_GLB_URL;
}

/** IEC 132 / 132S / 132M — alinhado a ``motor_familia_iec132_silhueta_somente_ficha`` (Python). */
export function iec132SomenteFichaMecanica(row: Record<string, unknown>): boolean {
  const rawU = `${carcacaFichaUpper(row)} ${carcacaBlob(row)}`.toUpperCase();
  if (!rawU.trim()) return false;
  const c = rawU.replace(/[\s._\-/]+/g, "");
  if (nema56SomenteFichaMecanica(row)) return false;
  if (/NEMA(?:\s*[-_]?\s*)?48\b/i.test(rawU)) return false;
  if (/NEMA(?:\s*[-_]?\s*)?42\b/i.test(rawU)) return false;
  const ui = row._consulta_ui;
  const uiObj = typeof ui === "object" && ui && !Array.isArray(ui) ? (ui as Record<string, unknown>) : null;
  const carOnly = String(uiObj?.carcaca ?? uiObj?.Carcaca ?? "")
    .replace(/[\s._\-/]+/g, "")
    .toUpperCase();
  if (carOnly.includes("B35") || carOnly.includes("B14") || carOnly.includes("B5")) return false;
  if (/\bIEC\W*132\b/i.test(rawU) || c.includes("IEC132")) return true;
  const b3Ok =
    c.includes("B3T") ||
    c.includes("B3D") ||
    c.includes("B3L") ||
    /(?<=[0-9LMSm])B3(?![0-9])/i.test(c);
  if (!b3Ok) return false;
  if (!c.includes("TEFC") && !/ALET|ALETADO|ALETAS/i.test(rawU)) return false;
  return /(?<![0-9.])132[MS](?![0-9])/i.test(c);
}

function strictNema56Mode(): boolean {
  return truthyEnv(
    readEnv("NEXT_PUBLIC_HOLOGRAM_CARCACA_NEMA56_STRICT", "HOLOGRAM_CARCACA_NEMA56_STRICT"),
  );
}

/**
 * URL do GLB para <model-viewer>, ou null (UI mostra aviso / futura malha procedural).
 */
export function resolveHologramGlbUrl(row: Record<string, unknown>): string | null {
  const motor = motorBlock(row);

  for (const key of ["holograma_glb_url", "holograma_glb", "HologramaGlbUrl"] as const) {
    const raw = motor[key];
    if (raw) {
      const u = String(raw).trim();
      if (/^https?:\/\//i.test(u) && pathLooksGlb(u)) return u;
    }
  }

  const mid = motorIdStr(row);
  if (mid) {
    const perMotor = readEnv(`NEXT_PUBLIC_HOLOGRAM_GLB_MOTOR_${mid}`, `HOLOGRAM_GLB_MOTOR_${mid}`);
    if (perMotor && /^https?:\/\//i.test(perMotor) && pathLooksGlb(perMotor)) return perMotor;
  }

  const strict = strictNema56Mode();
  const n56 = nema56SomenteFichaMecanica(row);
  const nema56Url = nema56GlbEfectivo();

  if (strict) {
    if (n56 && nema56Url) return nema56Url;
    if (nema42SomenteFichaMecanica(row)) {
      const u42 = nema42GlbEfectivo();
      if (u42) return u42;
    }
    if (iec132SomenteFichaMecanica(row)) {
      const u132 = iec132GlbEfectivo();
      if (u132) return u132;
    }
    return null;
  }

  if (n56 && nema56Url) return nema56Url;

  if (nema42SomenteFichaMecanica(row)) {
    const u42 = nema42GlbEfectivo();
    if (u42) return u42;
  }

  if (iec132SomenteFichaMecanica(row)) {
    const u132 = iec132GlbEfectivo();
    if (u132) return u132;
  }

  for (const name of [
    "NEXT_PUBLIC_HOLOGRAM_GLB_DEFAULT",
    "HOLOGRAM_GLB_DEFAULT",
    "NEXT_PUBLIC_HOLOGRAM_GLB_WEG_STYLE_HOUSING",
    "HOLOGRAM_GLB_WEG_STYLE_HOUSING",
  ] as const) {
    const u = readEnv(name);
    if (u && /^https?:\/\//i.test(u) && pathLooksGlb(u)) return u;
  }

  return null;
}

/** Ordem alinhada a `utils/motor_hologram.py` → HOLOGRAM_CHOICES. */
export const HOLOGRAM_PRESET_OPTIONS: { value: string; label: string }[] = [
  { value: "auto", label: "Automatico (IP + carcaca)" },
  { value: "generico", label: "Generico IEC" },
  { value: "ip55_iso", label: "IP55 fechado (aleta padrao)" },
  { value: "ip21_aberto", label: "IP21 / gotejamento" },
  { value: "liso_56", label: "Liso, peq., c/ pes (42, 48, 56, 56H-D-L-Y, mesma silh. 3D)" },
  { value: "cface_56", label: "NEMA 56C / 48C / C-face (flange)" },
  { value: "pump_56j", label: "Bomba / 56J (montagem diametro)" },
  { value: "nema_footless", label: "Sem pes / so face (silhueta distinta)" },
  { value: "nema_mono", label: "NEMA monofasico compacto (legado)" },
  { value: "iec_w22", label: "IEC ferro W22 / aletas densas" },
  { value: "trif_grande", label: "Trifasico grande porte" },
  { value: "servo_compacto", label: "IP66 / servo compacto" },
];

const _PRESET_LABEL_MAP: Record<string, string> = Object.fromEntries(
  HOLOGRAM_PRESET_OPTIONS.map((o) => [o.value, o.label]),
);

export function hologramPresetLabel(row: Record<string, unknown>): string {
  const motor = motorBlock(row);
  const explicit = String(motor.holograma_preset || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_");
  if (explicit && explicit !== "auto" && _PRESET_LABEL_MAP[explicit]) {
    return _PRESET_LABEL_MAP[explicit];
  }
  if (explicit && explicit !== "auto") return explicit;
  return _PRESET_LABEL_MAP.auto;
}
