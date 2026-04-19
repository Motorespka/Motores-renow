"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Store } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import type { MeResponse } from "@/lib/types";

/**
 * Paridade gradual com `page/hub_comercial.py` (Streamlit).
 * O módulo comercial usa persistência e moderação no backend Python — aqui só shell seguro.
 */
export default function HubComercialPage() {
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
      title="Hub comercial"
      subtitle="Classificados, empresas e vagas (em migração)"
      isAdmin={me.profile.is_admin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      <div className="max-w-2xl premium-card-elevated p-6 border border-border/40">
        <div className="flex items-center gap-3 text-primary">
          <Store className="w-6 h-6" />
          <span className="font-display text-sm tracking-wider">MÓDULO COMERCIAL</span>
        </div>
        <p className="mt-3 text-[12px] text-muted-foreground font-tech leading-relaxed">
          A versão completa (classificados, chat interno, termos e moderação) continua disponível no{" "}
          <strong className="text-foreground/90">Streamlit</strong> na rota Hub Comercial. Esta página no Next.js
          existe para navegação unificada e será preenchida à medida que APIs e UI forem portadas — sem alterar o
          comportamento do site legado.
        </p>
        <ul className="mt-4 text-[11px] text-muted-foreground space-y-2 list-disc pl-4">
          <li>Próximo passo sugerido: endpoints FastAPI ou Edge Functions para listagens públicas.</li>
          <li>Reutilizar regras de `services/modulo_comercial.py` no servidor antes de expor dados sensíveis.</li>
        </ul>
        <div className="mt-6 flex flex-wrap gap-2">
          <Link
            href="/dashboard"
            className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 transition-colors"
          >
            Painel
          </Link>
          <Link
            href="/conferencia"
            className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 transition-colors"
          >
            Conferência técnica
          </Link>
        </div>
      </div>
    </AppShell>
  );
}
