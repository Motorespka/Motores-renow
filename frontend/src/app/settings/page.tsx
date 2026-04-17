"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { KeyRound, Link2, ShieldCheck, Sliders } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { MeResponse, SettingsMeResponse } from "@/lib/types";
import { SUPABASE_CONFIGURED } from "@/lib/supabase";

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [prefs, setPrefs] = useState<SettingsMeResponse | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      const session = await requireSession(router);
      if (!session) return;
      try {
        const [mePayload, settingsPayload] = await Promise.all([
          apiFetch<MeResponse>("/auth/me", session.access_token),
          apiFetch<SettingsMeResponse>("/settings/me", session.access_token),
        ]);
        setMe(mePayload);
        setPrefs(settingsPayload);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Falha ao carregar configurações.";
        setError(msg);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  if (loading) return <div className="center-screen text-muted">Carregando configurações...</div>;
  if (!me) return <div className="center-screen error">{error || "Sessão inválida."}</div>;

  return (
    <AppShell
      title="Configurações"
      subtitle="Integrações, ambiente e preferências do workspace"
      isAdmin={me.profile.is_admin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      {error ? (
        <div className="mt-3 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
          {error}
        </div>
      ) : null}

      <div className="grid gap-3 lg:grid-cols-3">
        <div className="premium-card-elevated p-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-display text-sm tracking-wider">AUTH</div>
              <div className="text-[11px] text-muted-foreground font-tech mt-1">Estado do Supabase.</div>
            </div>
            <KeyRound className="w-4 h-4 text-primary" />
          </div>
          <div className="mt-4 premium-card p-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-muted-foreground font-tech">Supabase</span>
              <span className={SUPABASE_CONFIGURED ? "badge-premium badge-primary" : "badge-premium badge-warning"}>
                {SUPABASE_CONFIGURED ? "CONFIGURADO" : "DEV (SEM ENV)"}
              </span>
            </div>
            <div className="mt-2 text-[12px] text-muted-foreground font-tech">
              {SUPABASE_CONFIGURED
                ? "Login/roles ativos via Supabase Auth."
                : "Modo localhost sem senha habilitado. Configure env para produção."}
            </div>
          </div>
        </div>

        <div className="premium-card-elevated p-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-display text-sm tracking-wider">INTEGRAÇÕES</div>
              <div className="text-[11px] text-muted-foreground font-tech mt-1">URLs e serviços.</div>
            </div>
            <Link2 className="w-4 h-4 text-primary" />
          </div>

          <div className="mt-4 grid gap-2">
            <div className="premium-card p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-muted-foreground font-tech">Backend (API)</span>
                <span className="badge-premium badge-primary">NEXT_PUBLIC_API_BASE_URL</span>
              </div>
              <div className="mt-2 text-[11px] text-muted-foreground font-mono-tech">
                {process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api"}
              </div>
            </div>
            <div className="premium-card p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-muted-foreground font-tech">Perfil</span>
                <ShieldCheck className="w-4 h-4 text-primary" />
              </div>
              <div className="mt-2 text-[12px] text-muted-foreground font-tech">
                {me.profile.role} • {me.profile.plan} • {me.profile.tier}
              </div>
            </div>
          </div>
        </div>

        <div className="premium-card-elevated p-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-display text-sm tracking-wider">PREFERÊNCIAS</div>
              <div className="text-[11px] text-muted-foreground font-tech mt-1">UI/UX (placeholder).</div>
            </div>
            <Sliders className="w-4 h-4 text-primary" />
          </div>

          <div className="mt-4 premium-card p-4 text-[12px] text-muted-foreground font-tech">
            <div className="flex items-center justify-between gap-2">
              <span>Preferências do usuário (salvas no Supabase via FastAPI)</span>
              <button
                type="button"
                disabled={saving}
                onClick={async () => {
                  setSaving(true);
                  setError("");
                  try {
                    const session = await requireSession(router);
                    if (!session) return;
                    const updated = await apiFetch<SettingsMeResponse>("/settings/me", session.access_token, {
                      method: "PATCH",
                      body: JSON.stringify({ ui_prefs: { dashboardDensity: "comfortable" } }),
                    });
                    setPrefs(updated);
                  } catch (e) {
                    const msg = e instanceof Error ? e.message : "Falha ao salvar preferências.";
                    setError(msg);
                  } finally {
                    setSaving(false);
                  }
                }}
                className="text-[11px] px-3 py-2 rounded-xl border border-primary/25 bg-primary/15 hover:bg-primary/20 text-primary transition-colors disabled:opacity-60"
              >
                {saving ? "Salvando..." : "Salvar exemplo"}
              </button>
            </div>
            <div className="mt-3 text-[11px] text-muted-foreground font-mono-tech whitespace-pre-wrap break-words">
              {prefs ? JSON.stringify(prefs.ui_prefs || {}, null, 2) : "{}"}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

