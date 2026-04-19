import type { Metadata } from "next";
import Link from "next/link";
import { Cpu, Wrench } from "lucide-react";

import { MarketingNav } from "@/components/marketing/MarketingNav";
import { SalesWhatsAppButton } from "@/components/marketing/SalesWhatsAppButton";
import {
  checklistCampo,
  ENGENHARIA_WA_MSG,
  faqEng,
  focoTecnico,
  honestidade
} from "@/data/engenharia-pt";

export const metadata: Metadata = {
  title: "Manutenção elétrica · Moto-Renow",
  description:
    "Para técnicos e engenheiros de manutenção de motores elétricos: consulta, OS, conferência. Comercial por WhatsApp."
};

export default function EngenhariaPage() {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 grid-bg" />
      <MarketingNav />

      <main className="relative z-[1] mx-auto w-full max-w-5xl flex-1 px-5 py-10 pb-24">
        <p className="text-[10px] font-tech tracking-[0.22em] text-primary/80">TÉCNICO · ENGENHARIA DE MANUTENÇÃO</p>
        <h1 className="mt-2 font-display text-2xl font-bold tracking-wide text-foreground sm:text-3xl">
          Motores elétricos — manutenção
        </h1>
        <p className="mt-3 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
          Página para quem decide tecnicamente na bancada ou valida intervenções: o que a plataforma reforça no dia a
          dia da oficina de <strong className="text-foreground/90">motores elétricos</strong>, com linguagem directa e
          sem prometer o que está fora do âmbito.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <SalesWhatsAppButton size="lg" prefill={ENGENHARIA_WA_MSG}>
            Falar a nível técnico
          </SalesWhatsAppButton>
          <Link
            href="/funcionalidades"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-border/60 bg-muted/20 px-5 py-3 text-sm font-semibold tracking-wide text-foreground hover:bg-muted/35 transition-colors"
          >
            <Cpu className="h-4 w-4 text-primary shrink-0" />
            Mapa completo de funcionalidades
          </Link>
        </div>

        <section className="mt-14">
          <h2 className="font-display text-sm font-bold tracking-[0.18em] text-primary/90">Onde a ferramenta ajuda</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {focoTecnico.map((x) => (
              <div key={x.title} className="premium-card-elevated border border-border/45 p-5">
                <h3 className="font-display text-xs font-bold tracking-wide text-foreground">{x.title}</h3>
                <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground sm:text-[12px]">{x.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-14 premium-card-elevated border border-border/50 p-6">
          <h2 className="font-display text-sm font-bold tracking-wide text-foreground flex items-center gap-2">
            <Wrench className="h-4 w-4 text-accent" />
            Critério técnico
          </h2>
          <ul className="mt-4 space-y-2 text-[12px] text-muted-foreground leading-relaxed">
            {honestidade.map((line) => (
              <li key={line} className="flex gap-2">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary/70" aria-hidden />
                {line}
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-14">
          <h2 className="font-display text-sm font-bold tracking-[0.18em] text-primary/90">Checklist de campo (resumo)</h2>
          <ul className="mt-4 space-y-2 max-w-3xl text-[12px] text-muted-foreground leading-relaxed">
            {checklistCampo.map((line) => (
              <li key={line} className="flex gap-2">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent/80" aria-hidden />
                {line}
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-14">
          <h2 className="font-display text-sm font-bold tracking-[0.18em] text-primary/90">Perguntas frequentes</h2>
          <div className="mt-6 space-y-3 max-w-3xl">
            {faqEng.map((row) => (
              <div key={row.q} className="premium-card-elevated border border-border/40 p-4">
                <h3 className="font-display text-xs font-bold tracking-wide text-foreground">{row.q}</h3>
                <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground sm:text-[12px]">{row.a}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-14 premium-card-elevated border border-primary/25 bg-primary/5 p-6 sm:flex sm:items-center sm:justify-between gap-6">
          <p className="text-[12px] text-muted-foreground max-w-xl leading-relaxed">
            Quer alinhar profundidade técnica (planos, módulos, formação) com alguém da equipa? Use o WhatsApp — sem
            formulários de pagamento aqui.
          </p>
          <SalesWhatsAppButton size="lg" prefill={ENGENHARIA_WA_MSG} className="shrink-0 w-full sm:w-auto justify-center" />
        </section>

        <p className="mt-12 text-[11px] text-muted-foreground/80 font-tech">
          <Link href="/" className="text-primary/80 hover:underline">
            ← Início
          </Link>
          {" · "}
          <Link href="/para-oficinas" className="text-primary/80 hover:underline">
            Para oficinas (gestão)
          </Link>
          {" · "}
          <Link href="/planos" className="text-primary/80 hover:underline">
            Planos
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
