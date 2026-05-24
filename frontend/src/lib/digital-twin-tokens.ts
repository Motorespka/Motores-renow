/**
 * PMTH Digital Twin — tokens (espelho de design-system/digital-twin-tokens.json)
 * Ao alterar cores/limites físicos, atualize o JSON na raiz do monorepo.
 */
export const digitalTwinTokens = {
  colors: {
    bg0: "#0B1117",
    bg1: "#0E1419",
    panel: "#141C24",
    panelElevated: "#1A2430",
    ink: "#E9F7FF",
    inkSoft: "#9FB9CF",
    inkMuted: "#6B8499",
    cyan: "#00E5FF",
    cyanDim: "rgba(0, 229, 255, 0.14)",
    cyanGlow: "rgba(0, 229, 255, 0.35)",
    lime: "#DEFF9A",
    orange: "#FF8A00",
    green: "#3FB950",
    yellow: "#D29922",
    red: "#F85149",
    border: "rgba(0, 229, 255, 0.22)",
    borderStrong: "rgba(0, 229, 255, 0.45)",
  },
  physics: {
    bMaxT: 2.0,
    bLimitT: 1.5,
    jMaxAmm2: 8.0,
    jIdealAmm2: 4.0,
    jMinAmm2: 3.0,
    jHardMaxAmm2: 7.0,
    ffIdealLoPercent: 30,
    ffIdealHiPercent: 40,
    ffMinPercent: 25,
    ffMaxPercentLimit: 45,
  },
} as const;

export type ZoneStatus = "ok" | "warn" | "danger" | "muted";

export function zoneStatus(
  value: number | null | undefined,
  idealLo: number,
  idealHi: number,
  hardLo?: number,
  hardHi?: number,
): ZoneStatus {
  if (value == null || Number.isNaN(value)) return "muted";
  if (hardLo != null && value < hardLo) return "danger";
  if (hardHi != null && value > hardHi) return "danger";
  if (value >= idealLo && value <= idealHi) return "ok";
  return "warn";
}
