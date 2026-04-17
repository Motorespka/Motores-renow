import Link from "next/link";
import { ReactNode } from "react";

export function EmptyState({
  title,
  subtitle,
  icon,
  primaryAction,
  secondaryAction,
}: {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  primaryAction?: { label: string; href: string };
  secondaryAction?: { label: string; href: string };
}) {
  return (
    <div className="premium-card-elevated p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-display text-sm tracking-wider">{title}</div>
          {subtitle ? <div className="mt-1 text-[11px] text-muted-foreground font-tech">{subtitle}</div> : null}
        </div>
        {icon ? (
          <div className="w-10 h-10 rounded-xl border border-border/50 bg-muted/30 flex items-center justify-center">
            {icon}
          </div>
        ) : null}
      </div>

      {(primaryAction || secondaryAction) ? (
        <div className="mt-4 flex items-center gap-2 flex-wrap">
          {primaryAction ? (
            <Link
              href={primaryAction.href}
              className="h-10 px-4 rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors flex items-center justify-center"
            >
              {primaryAction.label}
            </Link>
          ) : null}
          {secondaryAction ? (
            <Link
              href={secondaryAction.href}
              className="h-10 px-4 rounded-xl bg-muted/30 border border-border/40 text-foreground/90 hover:bg-muted/50 transition-colors flex items-center justify-center"
            >
              {secondaryAction.label}
            </Link>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

