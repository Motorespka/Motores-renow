"use client";

import { cn } from "@/lib/utils";

export type VerdictBannerProps = {
  approved: boolean;
  title?: string;
  subtitle?: string;
  confidencePct?: number;
  deviationPct?: number;
  turnsPerCoil?: string | number;
  wireGauge?: string;
  stackLengthMm?: string | number;
};

export function DigitalTwinVerdictBanner({
  approved,
  title,
  subtitle,
  confidencePct,
  deviationPct,
  turnsPerCoil = "—",
  wireGauge = "—",
  stackLengthMm = "—",
}: VerdictBannerProps) {
  const resolvedTitle =
    title ??
    (approved ? "APROVADO — dentro da faixa OFICIAL" : "REPROVADO — limites físicos excedidos");
  const resolvedSub =
    subtitle ??
    (confidencePct != null
      ? `Confiança física ${confidencePct.toFixed(1)}%${
          deviationPct != null ? ` · desvio médio ±${deviationPct.toFixed(1)}%` : ""
        }`
      : "");

  return (
    <div className={cn("dt-verdict", approved ? "dt-verdict--ok" : "dt-verdict--danger")}>
      <div className="dt-verdict__icon">{approved ? "✓" : "✕"}</div>
      <div className="dt-verdict__body">
        <div className="dt-verdict__title">{resolvedTitle}</div>
        {resolvedSub ? <div className="dt-verdict__sub">{resolvedSub}</div> : null}
      </div>
      <div className="dt-verdict__metrics">
        <div className="dt-verdict__metric">
          <span className="dt-verdict__metric-label">ESPIRAS / BOBINA</span>
          <span className="dt-verdict__metric-value">{turnsPerCoil}</span>
        </div>
        <div className="dt-verdict__metric">
          <span className="dt-verdict__metric-label">BITOLA SUGERIDA</span>
          <span className="dt-verdict__metric-value dt-verdict__metric-value--accent">{wireGauge}</span>
        </div>
        <div className="dt-verdict__metric">
          <span className="dt-verdict__metric-label">LT</span>
          <span className="dt-verdict__metric-value">{stackLengthMm}</span>
        </div>
      </div>
    </div>
  );
}
