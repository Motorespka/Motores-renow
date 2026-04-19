import Link from "next/link";
import { BarChart3, ClipboardList, Cpu, ShieldCheck, Sparkles } from "lucide-react";

import { MarketingNav } from "@/components/marketing/MarketingNav";
import { SalesWhatsAppButton } from "@/components/marketing/SalesWhatsAppButton";

const WA_TRIAL =
  "Olá! Quero saber como experimentar a Moto-Renow na minha oficina (sem pagamento pelo site).";

const WA_PLANOS = "Olá! Quero entender planos e condições da Moto-Renow — prefiro acertar tudo por aqui.";

export function PublicHome() {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 grid-bg" />
      <div className="pointer-events-none absolute -top-32 left-[-120px] h-[480px] w-[480px] rounded-full bg-primary/10 blur-3xl" />
      <div className="pointer-events-none absolute -top-40 right-[-160px] h-[480px] w-[480px] rounded-full bg-accent/10 blur-3xl" />

      <MarketingNav />

      <main className="relative z-[1] mx-auto flex w-full max-w-5xl flex-1 flex-col gap-16 px-5 py-10 pb-20">
        <section className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-[10px] font-tech tracking-[0.2em] text-primary/90">
              <Sparkles className="h-3 w-3" />
              CONSULTA · OS · EQUIPA
            </p>
            <h1 className="mt-4 font-display text-2xl font-bold leading-tight tracking-wide text-foreground sm:text-3xl lg:text-4xl">
              Menos improviso na bancada. Mais rasto técnico na oficina.
            </h1>
            <p className="mt-4 max-w-xl text-[13px] leading-relaxed text-muted-foreground sm:text-sm">
              A Moto-Renow organiza fichas de motor, filas de trabalho e leitura técnica no mesmo sítio onde a
              equipa já opera. <strong className="text-foreground/90">Planos, faturação e dados sensíveis</strong>{" "}
              tratamos no <strong className="text-foreground/90">WhatsApp</strong> — aqui não pedimos cartão nem
              referências bancárias.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <SalesWhatsAppButton size="lg" prefill={WA_TRIAL}>
                Pedir demo / trial
              </SalesWhatsAppButton>
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-xl border border-border/60 bg-muted/20 px-5 py-3 text-sm font-semibold tracking-wide text-foreground hover:bg-muted/35 transition-colors"
              >
                Já tenho acesso
              </Link>
            </div>
            <p className="mt-4 text-[11px] text-muted-foreground/80 font-tech">
              Primeiro vê o fluxo no painel; depois combinamos o que faz sentido para a sua operação.
            </p>
            <p className="mt-2 text-[11px] font-tech flex flex-wrap gap-x-3 gap-y-1">
              <Link href="/para-oficinas" className="text-primary/85 hover:underline">
                Dono / gestor de oficina
              </Link>
              <span className="text-muted-foreground/50">·</span>
              <Link href="/engenharia" className="text-primary/85 hover:underline">
                Técnico · motores elétricos
              </Link>
            </p>
          </div>

          <div className="premium-card-elevated border border-border/50 p-5 sm:p-6">
            <p className="font-display text-[11px] font-bold tracking-[0.2em] text-primary/80">ANTES DE PAGAR NADA</p>
            <h2 className="mt-2 font-display text-sm font-bold tracking-wide text-foreground">O “wow” é operacional</h2>
            <ul className="mt-4 space-y-3 text-[12px] text-muted-foreground leading-relaxed">
              <li className="flex gap-2">
                <ClipboardList className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                Fila e estado das intervenções visíveis para a equipa — menos “quem pegou nisto?”.
              </li>
              <li className="flex gap-2">
                <Cpu className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                Consulta técnica com contexto de motor: menos voltar atrás na prateleira.
              </li>
              <li className="flex gap-2">
                <BarChart3 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                Indicadores simples no painel para perceber o que está a entupir a oficina.
              </li>
            </ul>
            <div className="mt-6 border-t border-border/40 pt-5">
              <SalesWhatsAppButton prefill={WA_PLANOS} className="w-full sm:w-auto">
                Planos e condições (WhatsApp)
              </SalesWhatsAppButton>
              <Link
                href="/planos"
                className="mt-3 block text-center text-[11px] font-tech text-primary hover:underline sm:text-left"
              >
                Ver página de planos (só texto)
              </Link>
              <Link
                href="/funcionalidades"
                className="mt-1 block text-center text-[11px] font-tech text-primary hover:underline sm:text-left"
              >
                Mapa completo: manutenção de motores + dono da oficina
              </Link>
            </div>
          </div>
        </section>

        <section>
          <h2 className="font-display text-sm font-bold tracking-[0.18em] text-primary/90">PORQUÊ NÃO É “MAIS UM PDF”</h2>
          <p className="mt-2 max-w-2xl text-[12px] text-muted-foreground leading-relaxed">
            Ferramenta pensada para oficina de motores: rotina de OS, histórico técnico e leitura orientada — não é um
            CRM genérico nem uma promessa de IA mágica. O que não cabe numa página web (contrato, faturação, dados
            pessoais além do login) fica para o canal humano.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            {[
              {
                icon: ShieldCheck,
                title: "Sem checkout aqui",
                body: "Nada de introduzir cartão ou IBAN nesta app. Comercial e condições acertam-se no WhatsApp."
              },
              {
                icon: Cpu,
                title: "Stack que já usa",
                body: "O ecossistema completo inclui fluxos no Streamlit da oficina; o Next.js concentra o que faz sentido no browser."
              },
              {
                icon: Sparkles,
                title: "Onboarding guiado",
                body: "Depois de combinarem o plano, indicamos o primeiro passo na plataforma — sem expor dados sensíveis na página pública."
              }
            ].map(({ icon: Icon, title, body }) => (
              <div key={title} className="premium-card-elevated border border-border/40 p-4">
                <Icon className="h-5 w-5 text-accent" />
                <h3 className="mt-3 font-display text-xs font-bold tracking-wide text-foreground">{title}</h3>
                <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">{body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="premium-card-elevated border border-border/50 p-6 text-center sm:text-left sm:flex sm:items-center sm:justify-between gap-6">
          <div>
            <h2 className="font-display text-sm font-bold tracking-wide text-foreground">Pronto para ver na prática?</h2>
            <p className="mt-2 text-[12px] text-muted-foreground max-w-lg">
              Diga-nos o tamanho da equipa e o que quer priorizar (consulta, OS ou conferência). Respondemos por
              WhatsApp com o próximo passo — sem recolher dados de pagamento aqui.
            </p>
          </div>
          <SalesWhatsAppButton size="lg" prefill={WA_TRIAL} className="shrink-0 w-full sm:w-auto justify-center">
            Conversar agora
          </SalesWhatsAppButton>
        </section>
      </main>

      <footer className="relative z-[1] border-t border-border/30 py-6 text-center text-[10px] text-muted-foreground/70 font-tech">
        Moto-Renow · acesso técnico em{" "}
        <Link href="/login" className="text-primary/80 hover:underline">
          /login
        </Link>
        {" · "}
        <Link href="/como-comecar" className="text-primary/80 hover:underline">
          Como começar
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
      </footer>
    </div>
  );
}
