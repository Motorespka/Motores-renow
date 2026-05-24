"use client";

import { digitalTwinTokens, type ZoneStatus } from "@/lib/digital-twin-tokens";
import { cn } from "@/lib/utils";

const zoneColor: Record<ZoneStatus, string> = {
  ok: digitalTwinTokens.colors.green,
  warn: digitalTwinTokens.colors.orange,
  danger: digitalTwinTokens.colors.red,
  muted: digitalTwinTokens.colors.inkMuted,
};

export function DigitalTwinArcGauge({
  label,
  value,
  max,
  unit = "",
  status = "ok",
  size = 148,
}: {
  label: string;
  value: number;
  max: number;
  unit?: string;
  status?: ZoneStatus;
  size?: number;
}) {
  const pct = max > 0 ? Math.min(1, Math.max(0, value / max)) : 0;
  const cx = size / 2;
  const cy = size * 0.58;
  const r = size * 0.38;
  const start = Math.PI;
  const end = Math.PI * (1 - pct);
  const x1 = cx + r * Math.cos(start);
  const y1 = cy - r * Math.sin(start);
  const x2 = cx + r * Math.cos(end);
  const y2 = cy - r * Math.sin(end);
  const largeArc = pct > 0.5 ? 1 : 0;
  const color = zoneColor[status];

  return (
    <div className={cn("dt-arc-gauge", `dt-arc-gauge--${status}`)}>
      <svg viewBox={`0 0 ${size} ${size * 0.72}`} width={size} height={size * 0.72} aria-hidden>
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="rgba(0,229,255,0.12)"
          strokeWidth={10}
          strokeLinecap="round"
        />
        <path
          d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
      </svg>
      <div className="dt-arc-gauge__value" style={{ color }}>
        {value.toFixed(2)}
        {unit}
      </div>
      <div className="dt-arc-gauge__label">{label}</div>
    </div>
  );
}
