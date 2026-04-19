import type { Metadata } from "next";
import Link from "next/link";
import { Check } from "lucide-react";

import { MarketingNav } from "@/components/marketing/MarketingNav";
import { SalesWhatsAppButton } from "@/components/marketing/SalesWhatsAppButton";

export const metadata: Metadata = {
  title: "Planos · Moto-Renow",
  description: "Visão dos planos Moto-Renow. Comercial e condições via WhatsApp — sem pagamento nesta página."
};

const WA_MSG =
  "Olá! Quero detalhe dos planos Moto-Renow (módulos, utilizadores e condições). Prefiro acertar tudo por WhatsApp.";

const tiers = [
  {
    name: "Essencial",
    blurb: "Consulta e registo técnico com foco em velocidade na bancada.",
    bullets: ["Leitura técnica orientada", "Histórico de motores", "Ideal para equipas pequenas"]
  },
  {
    name: "Oficina",
    blurb: "Operação diária: filas, OS e visibilidade para toda a equipa.",
    bullets: ["Painel e prioridades", "Fluxo de intervenções", "Coordenação entre técnicos"],
    highlight: true
  },
  {
    name: "Pro / Conferência",
    blurb: "Camadas avançadas e conferência técnica quando o volume exige.",
    bullets: ["Fluxos mais profundos", "Conferência e revisão", "A combinar consoante o caso"]
  }
];

export default function PlanosPage() {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 grid-bg" />
      <MarketingNav />

      <main className="relative z-[1] mx-auto w-full max-w-5xl flex-1 px-5 py-10 pb-20">
        <p className="text-[10px] font-tech tracking-[0.22em] text-primary/80">TRANSPARÊNCIA</p>
        <h1 className="mt-2 font-display text-2xl font-bold tracking-wide text-foreground sm:text-3xl">Planos</h1>
        <p className="mt-3 max-w-2xl text-[13px] leading-relaxed text-muted-foreground">
          Esta página resume <strong className="text-foreground/90">o que cada nível cobre em produto</strong>. Valores,
          faturação, NDA ou cláusulas específicas não constam aqui de propósito:{" "}
          <strong className="text-foreground/90">tratamos isso no WhatsApp</strong>, sem pedir dados de pagamento
          nesta aplicação.
        </p>

        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          {tiers.map((t) => (
            <div
              key={t.name}
              className={`premium-card-elevated flex flex-col border p-5 ${
                t.highlight ? "border-primary/40 shadow-[0_0_32px_rgba(var(--glow-primary-rgb),0.12)]" : "border-border/45"
              }`}
            >
              {t.highlight ? (
                <span className="badge-premium badge-primary w-fit text-[9px]">MAIS PEDIDO</span>
              ) : (
                <span className="h-5" />
              )}
              <h2 className="mt-3 font-display text-sm font-bold tracking-wide text-foreground">{t.name}</h2>
              <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">{t.blurb}</p>
              <ul className="mt-4 flex-1 space-y-2">
                {t.bullets.map((b) => (
                  <li key={b} className="flex gap-2 text-[11px] text-muted-foreground">
                    <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                    {b}
                  </li>
                ))}
              </ul>
              <div className="mt-6 border-t border-border/35 pt-4">
                <p className="text-[10px] font-tech uppercase tracking-wider text-muted-foreground/90">Investimento</p>
                <p className="mt-1 text-sm font-semibold text-foreground">Sob consulta</p>
                <p className="mt-1 text-[10px] text-muted-foreground/80">Combinado por WhatsApp</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 premium-card-elevated border border-border/50 p-6 sm:flex sm:items-center sm:justify-between gap-6">
          <div>
            <h2 className="font-display text-sm font-bold tracking-wide text-foreground">Quer proposta por escrito?</h2>
            <p className="mt-2 text-[12px] text-muted-foreground max-w-xl leading-relaxed">
              Envie mensagem com cidade, n.º aproximado de técnicos e o que quer priorizar. Devolvemos com o próximo
              passo — <strong className="text-foreground/85">sem formulários de pagamento</strong> neste site.
            </p>
          </div>
          <SalesWhatsAppButton size="lg" prefill={WA_MSG} className="shrink-0 w-full sm:w-auto justify-center mt-4 sm:mt-0">
            Pedir proposta
          </SalesWhatsAppButton>
        </div>

        <p className="mt-8 text-[11px] text-muted-foreground/80 font-tech">
          <Link href="/" className="text-primary/80 hover:underline">
            ← Início
          </Link>
          {" · "}
          <Link href="/funcionalidades" className="text-primary/80 hover:underline">
            Funcionalidades
          </Link>
          {" · "}
          <Link href="/para-oficinas" className="text-primary/80 hover:underline">
            Para oficinas
          </Link>
          {" · "}
          <Link href="/engenharia" className="text-primary/80 hover:underline">
            Manutenção elétrica
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
