"use client";

import "@/styles/digital-twin.css";

import { DigitalTwinCompareColumn, type WindingColumnData } from "./DigitalTwinCompareColumn";
import { DigitalTwinInsightsPanel, type PhysicsInsightData } from "./DigitalTwinInsightsPanel";
import { DigitalTwinVerdictBanner } from "./DigitalTwinVerdictBanner";

export type DigitalTwinDashboardProps = {
  approved: boolean;
  confidencePct?: number;
  deviationPct?: number;
  proposed: WindingColumnData & PhysicsInsightData;
  original: WindingColumnData;
  stackLengthMm?: string | number;
  onGeneratePdf?: () => void;
};

/**
 * Layout principal do Gêmeo Digital — espelha o mockup PMTH / Streamlit.
 */
export function DigitalTwinDashboard({
  approved,
  confidencePct,
  deviationPct,
  proposed,
  original,
  stackLengthMm,
  onGeneratePdf,
}: DigitalTwinDashboardProps) {
  return (
    <div className="dt-root space-y-4">
      <DigitalTwinVerdictBanner
        approved={approved}
        confidencePct={confidencePct}
        deviationPct={deviationPct}
        turnsPerCoil={proposed.turns}
        wireGauge={proposed.wire}
        stackLengthMm={stackLengthMm}
      />

      <div>
        <h3 className="text-[10px] uppercase tracking-[0.14em] text-primary font-display mb-2">
          Comparativo antes / depois
        </h3>
        <div className="dt-compare-grid">
          <DigitalTwinCompareColumn side="a" data={original} />
          <DigitalTwinCompareColumn side="b" data={proposed} />
        </div>
      </div>

      <DigitalTwinInsightsPanel data={proposed} />

      {onGeneratePdf ? (
        <button
          type="button"
          onClick={onGeneratePdf}
          className="h-11 w-full rounded-xl bg-primary/20 border border-primary/40 text-primary font-semibold tracking-wider text-sm hover:bg-primary/30 transition-colors"
        >
          Gerar Laudo PDF
        </button>
      ) : null}
    </div>
  );
}
