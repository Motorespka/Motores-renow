import Link from "next/link";

type Props = {
  id: string | number;
  title: string;
  subtitle?: string;
  /** Linha técnica opcional (ex.: UUID + badge de etapa no Streamlit). */
  motorId?: string;
  stageLabel: string;
  stageVariant?: "primary" | "accent" | "warning";
  progressPct: number; // 0..100
  eta?: string;
  cadastroSeq?: number;
};

export function QueueItem({
  id,
  title,
  subtitle,
  motorId,
  stageLabel,
  stageVariant = "primary",
  progressPct,
  eta,
  cadastroSeq,
}: Props) {
  const badgeClass =
    stageVariant === "accent"
      ? "badge-premium badge-accent"
      : stageVariant === "warning"
        ? "badge-premium badge-warning"
        : "badge-premium badge-primary";

  const href =
    cadastroSeq != null
      ? `/motors/${encodeURIComponent(String(id))}?cadastro_seq=${encodeURIComponent(String(cadastroSeq))}`
      : `/motors/${encodeURIComponent(String(id))}`;

  return (
    <div className="premium-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          {motorId ? (
            <>
              <div className="flex items-center gap-2 flex-wrap mb-0.5">
                <span className="text-[10px] font-mono-tech text-muted-foreground truncate max-w-[220px]">{motorId}</span>
                <span className={badgeClass}>{stageLabel}</span>
              </div>
              <div className="font-tech text-sm text-foreground truncate">{title}</div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <div className="font-tech text-sm text-foreground truncate">{title}</div>
              <span className={badgeClass}>{stageLabel}</span>
            </div>
          )}
          {subtitle ? <div className="text-[11px] text-muted-foreground font-tech mt-0.5 truncate">{subtitle}</div> : null}
        </div>
        <Link
          href={href}
          className="text-[11px] px-2 py-1 rounded-lg border border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors shrink-0"
        >
          Abrir
        </Link>
      </div>

      <div className="mt-3 flex items-center justify-between gap-3">
        <div className="flex-1">
          <div className="progress-premium">
            <div className="progress-premium-fill" style={{ width: `${Math.max(0, Math.min(100, progressPct))}%` }} />
          </div>
        </div>
        {eta ? <div className="text-[10px] text-muted-foreground font-mono-tech">{eta}</div> : null}
      </div>
    </div>
  );
}

