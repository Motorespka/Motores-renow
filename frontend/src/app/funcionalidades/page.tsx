import type { Metadata } from "next";
import Link from "next/link";

import { MarketingNav } from "@/components/marketing/MarketingNav";
import { SalesWhatsAppButton } from "@/components/marketing/SalesWhatsAppButton";
import { featureFaq, featureSections, FUNCIONALIDADES_WA_MSG } from "@/data/product-features-pt";

export const metadata: Metadata = {
  title: "Funcionalidades · Moto-Renow",
  description:
    "Visão de produto para oficinas: manutenção de motores, OS, qualidade e gestão. Comercial via WhatsApp — sem pagamento nesta página."
};

const tocLabel: Record<string, string> = {
  "donos-resumo": "Dono",
  "fluxo-30s": "Fluxo",
  "entrada-triagem": "Entrada",
  diagnostico: "Diagnóstico",
  "intervencao-os": "OS",
  "qualidade-entrega": "Qualidade",
  "stock-compras": "Stock",
  "cliente-comunicacao": "Cliente",
  "gestao-dono": "Gestão",
  diferenciacao: "Área técnica",
  "para-oficinas": "Segmentos",
  "conteudo-area": "Glossário",
  "materiais-decisao": "Decisão",
  "juridico-linha": "RGPD",
  "contacto-humano": "Suporte",
  "site-o-que-evitar": "Foco site",
  faq: "FAQ"
};

export default function FuncionalidadesPage() {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 grid-bg" />
      <MarketingNav />

      <main className="relative z-[1] mx-auto w-full max-w-5xl flex-1 px-5 py-10 pb-24">
        <p className="text-[10px] font-tech tracking-[0.22em] text-primary/80">PRODUTO · MANUTENÇÃO DE MOTORES</p>
        <h1 className="mt-2 font-display text-2xl font-bold tracking-wide text-foreground sm:text-3xl">Funcionalidades</h1>
        <p className="mt-3 max-w-3xl text-[13px] leading-relaxed text-muted-foreground">
          Lista consolidada do que a Moto-Renow visa suportar na oficina: desde a triagem do motor até indicadores para o
          dono. Nem tudo estará disponível na mesma versão — use como{" "}
          <strong className="text-foreground/90">mapa de conversa</strong> com a equipa. Para planos e condições,{" "}
          <strong className="text-foreground/90">WhatsApp</strong>; aqui não há checkout nem dados de pagamento.
        </p>

        <div className="mt-8 flex flex-wrap gap-2">
          <SalesWhatsAppButton size="lg" prefill={FUNCIONALIDADES_WA_MSG}>
            Alinhar roadmap com a equipa
          </SalesWhatsAppButton>
          <Link
            href="/planos"
            className="inline-flex items-center justify-center rounded-xl border border-border/60 bg-muted/20 px-5 py-3 text-sm font-semibold tracking-wide text-foreground hover:bg-muted/35 transition-colors"
          >
            Ver planos
          </Link>
        </div>

        <nav
          aria-label="Secções"
          className="mt-10 flex flex-wrap gap-1.5 rounded-xl border border-border/40 bg-muted/15 p-3"
        >
          {featureSections.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="rounded-lg border border-transparent px-2.5 py-1 text-[10px] font-tech tracking-wide text-muted-foreground hover:border-primary/25 hover:bg-primary/10 hover:text-primary transition-colors"
            >
              {tocLabel[s.id] ?? s.title.slice(0, 12)}
            </a>
          ))}
          <a
            href="#faq"
            className="rounded-lg border border-transparent px-2.5 py-1 text-[10px] font-tech tracking-wide text-muted-foreground hover:border-primary/25 hover:bg-primary/10 hover:text-primary transition-colors"
          >
            FAQ
          </a>
        </nav>

        <div className="mt-12 space-y-14">
          {featureSections.map((section) => (
            <section key={section.id} id={section.id} className="scroll-mt-24">
              {section.eyebrow ? (
                <p className="text-[10px] font-tech tracking-[0.2em] text-primary/75">{section.eyebrow}</p>
              ) : null}
              <h2 className="mt-1 font-display text-lg font-bold tracking-wide text-foreground sm:text-xl">
                {section.title}
              </h2>
              {section.lead ? (
                <p className="mt-2 max-w-3xl text-[12px] leading-relaxed text-muted-foreground sm:text-[13px]">
                  {section.lead}
                </p>
              ) : null}
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {section.blocks.map((block) => (
                  <div key={block.title} className="premium-card-elevated border border-border/45 p-4 sm:p-5">
                    <h3 className="font-display text-[11px] font-bold tracking-[0.12em] text-foreground/95">
                      {block.title}
                    </h3>
                    <ul className="mt-3 space-y-2 text-[11px] leading-relaxed text-muted-foreground sm:text-[12px]">
                      {block.items.map((item) => (
                        <li key={item} className="flex gap-2">
                          <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary/70" aria-hidden />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>

        <section id="faq" className="scroll-mt-24 mt-16 border-t border-border/40 pt-14">
          <p className="text-[10px] font-tech tracking-[0.2em] text-primary/75">FAQ · DONO</p>
          <h2 className="mt-1 font-display text-lg font-bold tracking-wide text-foreground">Perguntas frequentes</h2>
          <div className="mt-6 space-y-4 max-w-3xl">
            {featureFaq.map((row) => (
              <div key={row.q} className="premium-card-elevated border border-border/40 p-4">
                <h3 className="font-display text-xs font-bold tracking-wide text-foreground">{row.q}</h3>
                <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground sm:text-[12px]">{row.a}</p>
              </div>
            ))}
          </div>
        </section>

        <p className="mt-14 text-[11px] text-muted-foreground/80 font-tech">
          <Link href="/" className="text-primary/80 hover:underline">
            ← Início
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
          <Link href="/atualizacoes" className="text-primary/80 hover:underline">
            Atualizações
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
