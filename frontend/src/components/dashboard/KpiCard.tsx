import { ReactNode } from "react";

type Props = {
  label: string;
  value: string;
  delta?: string;
  badge?: { text: string; variant?: "primary" | "accent" | "warning" };
  icon?: ReactNode;
};

export function KpiCard({ label, value, delta, badge, icon }: Props) {
  const variant = badge?.variant || "primary";
  const badgeClass =
    variant === "accent" ? "badge-premium badge-accent" : variant === "warning" ? "badge-premium badge-warning" : "badge-premium badge-primary";

  return (
    <div className="premium-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[11px] text-muted-foreground tracking-wide font-tech">{label}</div>
          <div className="mt-1 flex items-end gap-2">
            <div className="font-display text-lg tracking-wider text-foreground">{value}</div>
            {delta ? <div className="text-[11px] text-muted-foreground font-mono-tech">{delta}</div> : null}
          </div>
        </div>
        <div className="shrink-0 flex items-center gap-2">
          {badge ? <span className={badgeClass}>{badge.text}</span> : null}
          {icon ? (
            <div className="w-9 h-9 rounded-xl border border-border/50 bg-muted/30 flex items-center justify-center">
              {icon}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

