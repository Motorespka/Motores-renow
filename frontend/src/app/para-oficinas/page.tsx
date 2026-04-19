import type { Metadata } from "next";
import Link from "next/link";
import { Building2, ClipboardCheck, MessageCircle } from "lucide-react";

import { MarketingNav } from "@/components/marketing/MarketingNav";
import { SalesWhatsAppButton } from "@/components/marketing/SalesWhatsAppButton";
import {
  doresTipicas,
  faqDono,
  oQueAjudamos,
  PARA_OFICINAS_WA_MSG,
  transparencia
} from "@/data/para-oficinas-pt";

export const metadata: Metadata = {
  title: "Para oficinas · Moto-Renow",
  description:
    "Informação para donos e gestores de oficina de motores: dores comuns, transparência e contacto. Sem pagamento neste site."
};

export default function ParaOficinasPage() {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 grid-bg" />
      <MarketingNav />

      <main className="relative z-[1] mx-auto w-full max-w-5xl flex-1 px-5 py-10 pb-24">
        <p className="text-[10px] font-tech tracking-[0.22em] text-primary/80">DONO · GESTOR</p>
        <h1 className="mt-2 font-display text-2xl font-bold tracking-wide text-foreground sm:text-3xl">
          Para oficinas
        </h1>
        <p className="mt-3 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
          Se decide orçamentos, prazos e equipa, isto é para si: o que costuma doer na manutenção de motores, como a
          Moto-Renow ajuda a ganhar controlo operacional, e como avançar <strong className="text-foreground/90">sem</strong>{" "}
          expor dados sensíveis ou pagamentos nesta página.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <SalesWhatsAppButton size="lg" prefill={PARA_OFICINAS_WA_MSG}>
            Falar como dono de oficina
          </SalesWhatsAppButton>
          <Link
            href="/engenharia"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-border/60 bg-muted/20 px-5 py-3 text-sm font-semibold tracking-wide text-foreground hover:bg-muted/35 transition-colors"
          >
            Técnicos · motores elétricos
          </Link>
          <Link
            href="/funcionalidades"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-border/60 bg-muted/20 px-5 py-3 text-sm font-semibold tracking-wide text-foreground hover:bg-muted/35 transition-colors"
          >
            <ClipboardCheck className="h-4 w-4 text-primary shrink-0" />
            Mapa de funcionalidades
          </Link>
        </div>

        <section className="mt-14">
          <h2 className="font-display text-sm font-bold tracking-[0.18em] text-primary/90">
            O QUE COSTUMA DOER (E NÃO É “FALTA DE VONTADE”)
          </h2>
          <ul className="mt-4 grid gap-3 sm:grid-cols-2">
            {doresTipicas.map((t) => (
              <li
                key={t}
                className="premium-card-elevated flex gap-3 border border-border/40 p-4 text-[12px] leading-relaxed text-muted-foreground"
              >
                <Building2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" aria-hidden />
                {t}
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-14">
          <h2 className="font-display text-sm font-bold tracking-[0.18em] text-primary/90">O QUE GANHA COM A FERRAMENTA</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {oQueAjudamos.map((x) => (
              <div key={x.title} className="premium-card-elevated border border-border/45 p-5">
                <h3 className="font-display text-xs font-bold tracking-wide text-foreground">{x.title}</h3>
                <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground sm:text-[12px]">{x.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-14 premium-card-elevated border border-border/50 p-6">
          <h2 className="font-display text-sm font-bold tracking-wide text-foreground flex items-center gap-2">
            <MessageCircle className="h-4 w-4 text-emerald-400/90" />
            Comercial e dados sensíveis
          </h2>
          <ul className="mt-4 space-y-2 text-[12px] text-muted-foreground leading-relaxed">
            {transparencia.map((line) => (
              <li key={line} className="flex gap-2">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary/70" aria-hidden />
                {line}
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-14">
          <h2 className="font-display text-sm font-bold tracking-[0.18em] text-primary/90">Perguntas de gestão</h2>
          <div className="mt-6 space-y-3 max-w-3xl">
            {faqDono.map((row) => (
              <div key={row.q} className="premium-card-elevated border border-border/40 p-4">
                <h3 className="font-display text-xs font-bold tracking-wide text-foreground">{row.q}</h3>
                <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground sm:text-[12px]">{row.a}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-14 premium-card-elevated border border-primary/25 bg-primary/5 p-6 sm:flex sm:items-center sm:justify-between gap-6">
          <p className="text-[12px] text-muted-foreground max-w-xl leading-relaxed">
            Quer uma conversa curta com o tamanho da equipa e o que quer priorizar? Envie mensagem — combinamos o
            próximo passo <strong className="text-foreground/90">sem formulários de pagamento</strong> aqui.
          </p>
          <SalesWhatsAppButton size="lg" prefill={PARA_OFICINAS_WA_MSG} className="shrink-0 w-full sm:w-auto justify-center" />
        </section>

        <p className="mt-12 text-[11px] text-muted-foreground/80 font-tech">
          <Link href="/" className="text-primary/80 hover:underline">
            ← Início
          </Link>
          {" · "}
          <Link href="/funcionalidades" className="text-primary/80 hover:underline">
            Funcionalidades
          </Link>
          {" · "}
          <Link href="/engenharia" className="text-primary/80 hover:underline">
            Manutenção elétrica
          </Link>
          {" · "}
          <Link href="/planos" className="text-primary/80 hover:underline">
            Planos
          </Link>
          {" · "}
          <Link href="/como-comecar" className="text-primary/80 hover:underline">
            Como começar
          </Link>
          {" · "}
          <Link href="/login" className="text-primary/80 hover:underline">
            Entrar
          </Link>
        </p>
      </main>
    </div>
  );
}
