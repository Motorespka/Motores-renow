"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { CHANGELOG, DEV_PREVIEW_CHANGELOG } from "@/data/changelog";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import type { MeResponse } from "@/lib/types";

function showDevPreviewNotes(): boolean {
  return process.env.NEXT_PUBLIC_DEV_RELEASE_NOTES === "1";
}

export default function AtualizacoesPage() {
  const router = useRouter();
  const [me, setMe] = useState<MeResponse | null>(null);

  useEffect(() => {
    (async () => {
      const session = await requireSession(router);
      if (!session) return;
      const mePayload = await apiFetch<MeResponse>("/auth/me", session.access_token);
      setMe(mePayload);
    })();
  }, [router]);

  if (!me) {
    return <div className="center-screen text-muted">Carregando…</div>;
  }

  return (
    <AppShell
      title="Atualizações do sistema"
      subtitle="O que mudou na plataforma — linguagem clara para a oficina"
      isAdmin={me.profile.is_admin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      <div className="mb-6 rounded-2xl border border-border/40 bg-gradient-to-br from-primary/[0.06] to-transparent p-5">
        <div className="flex items-center gap-2 text-primary">
          <Sparkles className="w-5 h-5" />
          <span className="text-[10px] font-semibold tracking-[0.2em]">RELEASE NOTES</span>
        </div>
        <h2 className="mt-2 font-display text-lg tracking-wide text-foreground">Atualizações do sistema</h2>
        <p className="mt-1 text-[12px] text-muted-foreground max-w-2xl leading-relaxed">
          Lista alinhada com a app da oficina. Versões antigas podem ainda mostrar algum termo técnico nas notas; as
          entradas novas privilegiam o que importa para quem trabalha na bancada e na gestão.
        </p>
      </div>

      {showDevPreviewNotes() && DEV_PREVIEW_CHANGELOG.length ? (
        <div className="mb-6 space-y-3">
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-[11px] text-amber-100">
            Pré-release (development) — mesmo bloco opcional que o Streamlit em modo dev.
          </div>
          {DEV_PREVIEW_CHANGELOG.map((item) => (
            <article
              key={`dev-${item.versao}`}
              className="premium-card-elevated p-5 border border-amber-500/20"
            >
              <div className="text-[10px] font-mono-tech text-amber-200/90 tracking-wider">
                PREVIEW · {item.versao} · {item.data}
              </div>
              <h3 className="mt-1 font-display text-sm tracking-wide text-foreground">{item.titulo}</h3>
              <div className="mt-3 text-[11px] text-muted-foreground space-y-2">
                {item.adicoes.length ? (
                  <ul className="list-disc pl-4 space-y-1">
                    {item.adicoes.map((row, i) => (
                      <li key={i}>{row}</li>
                    ))}
                  </ul>
                ) : null}
                {item.correcoes.length ? (
                  <ul className="list-disc pl-4 space-y-1">
                    {item.correcoes.map((row, i) => (
                      <li key={i}>{row}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </article>
          ))}
          <h3 className="font-display text-sm tracking-wider text-foreground pt-2">Releases gerais</h3>
        </div>
      ) : null}

      <div className="space-y-4">
        {CHANGELOG.map((item) => (
          <article
            key={item.versao}
            className="premium-card-elevated p-5 border border-border/35"
          >
            <div className="text-[10px] font-mono-tech text-primary/80 tracking-wider">
              {item.versao} · {item.data}
            </div>
            <h3 className="mt-1 font-display text-sm tracking-wide text-foreground">{item.titulo}</h3>

            <div className="mt-3 text-[11px]">
              <div className="font-semibold text-muted-foreground tracking-wide mb-1">Novidades</div>
              {item.adicoes.length ? (
                <ul className="list-disc pl-4 space-y-1 text-muted-foreground leading-relaxed">
                  {item.adicoes.map((row, i) => (
                    <li key={i}>{row}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted-foreground/70">Sem novidades nesta versão.</p>
              )}
            </div>

            <div className="mt-3 text-[11px]">
              <div className="font-semibold text-muted-foreground tracking-wide mb-1">Correções e melhorias</div>
              {item.correcoes.length ? (
                <ul className="list-disc pl-4 space-y-1 text-muted-foreground leading-relaxed">
                  {item.correcoes.map((row, i) => (
                    <li key={i}>{row}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted-foreground/70">Sem correções registradas.</p>
              )}
            </div>
          </article>
        ))}
      </div>

      <div className="mt-8 text-[11px] text-muted-foreground">
        <Link href="/dashboard" className="text-primary hover:underline">
          Voltar ao painel
        </Link>
      </div>
    </AppShell>
  );
}
