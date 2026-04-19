import type { Metadata } from "next";
import Link from "next/link";
import { ListOrdered } from "lucide-react";

import { MarketingNav } from "@/components/marketing/MarketingNav";
import { SalesWhatsAppButton } from "@/components/marketing/SalesWhatsAppButton";

export const metadata: Metadata = {
  title: "Como começar · Moto-Renow",
  description: "Primeiros passos na Moto-Renow. Acesso técnico e comercial separado do canal WhatsApp."
};

const WA_ONBOARD =
  "Olá! Já tenho / quero acesso Moto-Renow e preciso de ajuda com o primeiro passo (login ou oficina).";

const steps = [
  {
    title: "Combinar o plano no WhatsApp",
    text: "Dizemos que módulos fazem sentido e como fica o arranque. Nada de cartão nem dados bancários nesta app."
  },
  {
    title: "Receber credenciais ou convite",
    text: "O acesso técnico passa pelo fluxo normal de conta (email e senha). Guarde credenciais como faria com qualquer sistema da oficina."
  },
  {
    title: "Entrar e percorrer o painel",
    text: "Comece pelo painel e pela fila: é onde a equipa sente o ritmo. Depois aprofunde consulta e fichas de motor."
  },
  {
    title: "Alinhar hábitos da oficina",
    text: "Se já usa o Streamlit da oficina para alguns fluxos, mantenha o que funciona; o Next.js complementa o que quiser ver no browser."
  }
];

export default function ComoComecarPage() {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 grid-bg" />
      <MarketingNav />

      <main className="relative z-[1] mx-auto w-full max-w-3xl flex-1 px-5 py-10 pb-20">
        <p className="text-[10px] font-tech tracking-[0.22em] text-primary/80">ONBOARDING</p>
        <h1 className="mt-2 font-display text-2xl font-bold tracking-wide text-foreground">Como começar</h1>
        <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
          Resumo objetivo do arranque. Dúvidas comerciais ou sensíveis continuam no{" "}
          <strong className="text-foreground/90">WhatsApp</strong> — aqui só orientação de produto.
        </p>

        <ol className="mt-10 space-y-5">
          {steps.map((s, i) => (
            <li
              key={s.title}
              className="premium-card-elevated flex gap-4 border border-border/45 p-4 sm:p-5"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 font-display text-xs font-bold text-primary">
                {i + 1}
              </div>
              <div>
                <h2 className="font-display text-xs font-bold tracking-wide text-foreground sm:text-sm">{s.title}</h2>
                <p className="mt-2 text-[12px] leading-relaxed text-muted-foreground">{s.text}</p>
              </div>
            </li>
          ))}
        </ol>

        <div className="mt-10 flex flex-wrap items-center gap-3">
          <SalesWhatsAppButton size="lg" prefill={WA_ONBOARD}>
            Ajudem-me a começar
          </SalesWhatsAppButton>
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-xl border border-border/60 bg-muted/20 px-5 py-3 text-sm font-semibold tracking-wide text-foreground hover:bg-muted/35 transition-colors"
          >
            Ir para o login
          </Link>
        </div>

        <p className="mt-10 flex items-start gap-2 text-[11px] text-muted-foreground/90 font-tech">
          <ListOrdered className="mt-0.5 h-4 w-4 shrink-0 text-primary/70" />
          <span>
            Lista genérica; o seu caso pode ter passos extra (integrações, formação de equipa) — combinamos no canal
            direto.
          </span>
        </p>

        <p className="mt-6 text-[11px] text-muted-foreground/80 font-tech">
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
          <Link href="/planos" className="text-primary/80 hover:underline">
            Planos
          </Link>
        </p>
      </main>
    </div>
  );
}
