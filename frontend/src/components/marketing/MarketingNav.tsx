import Link from "next/link";

const linkCls =
  "text-[11px] font-tech tracking-wide text-muted-foreground hover:text-primary transition-colors px-2 py-1 rounded-lg hover:bg-primary/5";

export function MarketingNav() {
  return (
    <header className="relative z-10 border-b border-border/40 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-primary/90 to-primary/70 shadow-lg">
            <span className="font-display text-[11px] font-bold tracking-widest text-primary-foreground">MR</span>
          </div>
          <div className="flex flex-col leading-tight">
            <span className="font-display text-xs font-bold tracking-wider text-foreground">MOTO-RENOW</span>
            <span className="text-[9px] text-primary/70 tracking-[0.18em]">PLATAFORMA TÉCNICA</span>
          </div>
        </Link>
        <nav className="flex flex-wrap items-center justify-end gap-1 sm:gap-2">
          <Link href="/para-oficinas" className={linkCls}>
            Para oficinas
          </Link>
          <Link href="/engenharia" className={linkCls}>
            Manutenção elétrica
          </Link>
          <Link href="/funcionalidades" className={linkCls}>
            Funcionalidades
          </Link>
          <Link href="/planos" className={linkCls}>
            Planos
          </Link>
          <Link href="/como-comecar" className={linkCls}>
            Como começar
          </Link>
          <Link
            href="/login"
            className="text-[11px] font-tech tracking-wide rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-primary hover:bg-primary/15 transition-colors"
          >
            Entrar
          </Link>
        </nav>
      </div>
    </header>
  );
}
