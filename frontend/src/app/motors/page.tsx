"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Search } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { MeResponse, MotorListResponse } from "@/lib/types";

export default function MotorsPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [payload, setPayload] = useState<MotorListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");

  async function loadData(search: string, accessToken?: string) {
    const tokenResolved = accessToken || token;
    if (!tokenResolved) return;
    setLoading(true);
    setError("");
    try {
      const query = search ? `?q=${encodeURIComponent(search)}&limit=50` : "?limit=50";
      const list = await apiFetch<MotorListResponse>(`/motors${query}`, tokenResolved);
      setPayload(list);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Falha ao carregar motores.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    (async () => {
      const session = await requireSession(router);
      if (!session) return;
      setToken(session.access_token);
      try {
        const mePayload = await apiFetch<MeResponse>("/auth/me", session.access_token);
        setMe(mePayload);
      } catch {
        router.replace("/login");
        return;
      }
      await loadData("", session.access_token);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  function onSearch(event: FormEvent) {
    event.preventDefault();
    void loadData(q);
  }

  if (!me) {
    return <div className="center-screen text-muted">Carregando consulta...</div>;
  }

  const isAdmin = me.profile.is_admin;
  const mode = payload?.mode || "teaser";
  return (
    <AppShell
      title="Consulta de Motores"
      subtitle={mode === "teaser" ? "Modo teaser (free)" : "Modo completo (pago/admin)"}
      isAdmin={isAdmin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      <div className="premium-card-elevated p-5">
        <div className="flex items-center justify-between gap-2">
          <div>
            <div className="font-display text-sm tracking-wider">CONSULTA TÉCNICA</div>
            <div className="text-[11px] text-muted-foreground font-tech mt-1">
              Busque por marca, modelo, potência, RPM e outros campos.
            </div>
          </div>
          <span className={mode === "teaser" ? "badge-premium badge-warning" : "badge-premium badge-primary"}>
            {mode === "teaser" ? "TEASER" : "FULL"}
          </span>
        </div>

        <form onSubmit={onSearch} className="mt-4 flex gap-2 flex-wrap">
          <div className="flex-1 min-w-[240px] relative">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              className="w-full h-10 pl-9 pr-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar por marca, modelo, potência, RPM..."
            />
          </div>
          <button
            className="h-10 px-4 rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors"
            type="submit"
          >
            Buscar
          </button>
        </form>
      </div>

      {mode === "teaser" ? (
        <div className="mt-3 premium-card p-4">
          <div className="flex items-center justify-between gap-2">
            <span className="badge-premium badge-warning">MODO TEASER</span>
            <span className="text-[10px] text-muted-foreground font-mono-tech">limitado</span>
          </div>
          <p className="text-[12px] text-muted-foreground font-tech mt-2">
            Sua conta está em visualização limitada. Ative plano pago para detalhes e diagnóstico.
          </p>
        </div>
      ) : null}

      {error ? (
        <div className="mt-3 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
          {error}
        </div>
      ) : null}
      {loading ? <div className="mt-3 text-[12px] text-muted-foreground font-tech">Carregando...</div> : null}

      <div className="mt-3 grid gap-3">
        {(payload?.items || []).map((m) => (
          <div key={String(m.id)} className="premium-card p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <div className="font-tech text-sm text-foreground truncate">
                    {String(m.marca || "Motor")} {String(m.modelo || "-")}
                  </div>
                  <span className="badge-premium badge-primary">MOTOR</span>
                </div>
                <div className="text-[11px] text-muted-foreground font-tech mt-0.5 truncate">
                  {String(m.potencia || "-")} • {String(m.rpm || "-")}
                </div>
              </div>

              {mode === "full" ? (
                <Link
                  href={`/motors/${m.id}`}
                  className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors shrink-0"
                >
                  Detalhes
                </Link>
              ) : (
                <span className="text-[11px] px-3 py-2 rounded-xl border border-border/30 bg-muted/10 text-muted-foreground shrink-0">
                  Upgrade
                </span>
              )}
            </div>
          </div>
        ))}
        {!loading && !(payload?.items || []).length ? (
          <div className="premium-card p-4 text-[12px] text-muted-foreground font-tech">
            Nenhum motor encontrado.
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
