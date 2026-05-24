"use client";

import { DigitalTwinArcGauge } from "./DigitalTwinArcGauge";
import { digitalTwinTokens, zoneStatus } from "@/lib/digital-twin-tokens";

export type PhysicsInsightData = {
  jAmm2: number | null;
  ff: number | null;
  bTesla: number | null;
  copperAreaPerTurn?: number | null;
  copperAreaTotal?: number | null;
};

export function DigitalTwinInsightsPanel({ data }: { data: PhysicsInsightData }) {
  const pv = digitalTwinTokens.physics;
  const j = data.jAmm2 ?? 0;
  const ffPct = (data.ff ?? 0) * 100;
  const b = data.bTesla ?? 0;

  const jStatus = zoneStatus(data.jAmm2, pv.jMinAmm2, pv.jIdealAmm2 + 1, undefined, pv.jHardMaxAmm2);
  const ffStatus = zoneStatus(
    data.ff,
    pv.ffIdealLoPercent / 100,
    pv.ffIdealHiPercent / 100,
    pv.ffMinPercent / 100,
    pv.ffMaxPercentLimit / 100,
  );
  const bStatus = zoneStatus(data.bTesla, 0, pv.bLimitT, undefined, 1.8);

  return (
    <div className="dt-insights-panel">
      <div className="dt-insights-panel__title">Insights Físicos</div>
      <div className="dt-gauge-row">
        <DigitalTwinArcGauge
          label="Densidade de Corrente [J]"
          value={j}
          max={pv.jMaxAmm2}
          unit=" A/mm²"
          status={jStatus}
        />
        <DigitalTwinArcGauge
          label="Fator de Enchimento [ff]"
          value={ffPct}
          max={50}
          unit=" ff"
          status={ffStatus}
        />
        <DigitalTwinArcGauge
          label="Saturação Magnética [B]"
          value={b}
          max={pv.bMaxT}
          unit=" T"
          status={bStatus}
        />
      </div>
    </div>
  );
}
