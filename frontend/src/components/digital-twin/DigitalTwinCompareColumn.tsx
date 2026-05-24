"use client";

import { digitalTwinTokens, zoneStatus, type ZoneStatus } from "@/lib/digital-twin-tokens";
import { cn } from "@/lib/utils";

export type WindingColumnData = {
  badge: string;
  title: string;
  turns: string | number;
  wire: string;
  jAmm2: number | null;
  ff: number | null;
};

function barWidth(value: number | null, max: number): number {
  if (value == null || max <= 0) return 0;
  return Math.min(100, Math.max(0, (value / max) * 100));
}

export function DigitalTwinCompareColumn({
  side,
  data,
}: {
  side: "a" | "b";
  data: WindingColumnData;
}) {
  const pv = digitalTwinTokens.physics;
  const jStatus = zoneStatus(data.jAmm2, pv.jMinAmm2, pv.jIdealAmm2 + 1, undefined, pv.jHardMaxAmm2);
  const ffStatus = zoneStatus(
    data.ff,
    pv.ffIdealLoPercent / 100,
    pv.ffIdealHiPercent / 100,
    pv.ffMinPercent / 100,
    pv.ffMaxPercentLimit / 100,
  );

  return (
    <div className={cn("dt-compare-col", `dt-compare-col--${side}`)}>
      <div className="dt-compare-col__badge">{data.badge}</div>
      <div className="dt-compare-col__title">{data.title}</div>
      <CompareStat label="Espiras" value={data.turns} />
      <CompareStat label="Bitola" value={data.wire} />
      <CompareBar
        label="J · densidade"
        display={data.jAmm2 != null ? `${data.jAmm2.toFixed(2)} A/mm²` : "—"}
        width={barWidth(data.jAmm2, pv.jMaxAmm2)}
        status={jStatus}
      />
      <CompareBar
        label="ff · enchimento"
        display={data.ff != null ? `${(data.ff * 100).toFixed(1)}%` : "—"}
        width={barWidth(data.ff, pv.ffMaxPercentLimit / 100)}
        status={ffStatus}
      />
    </div>
  );
}

function CompareStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="dt-compare-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function CompareBar({
  label,
  display,
  width,
  status,
}: {
  label: string;
  display: string;
  width: number;
  status: ZoneStatus;
}) {
  return (
    <div className={cn("dt-compare-bar", `dt-compare-bar--${status}`)}>
      <div className="dt-compare-bar__label">{label}</div>
      <div className="dt-compare-bar__track">
        <div style={{ width: `${width}%` }} />
      </div>
      <div className="dt-compare-bar__val">{display}</div>
    </div>
  );
}
