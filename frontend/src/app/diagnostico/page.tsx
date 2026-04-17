"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Activity, FlaskConical, Wrench } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { EmptyState } from "@/components/EmptyState";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { DiagnosticListResponse, DiagnosticRunResponse, MeResponse, MotorListResponse, MotorRecord } from "@/lib/types";

function scoreFor(m: MotorRecord, idx: number): number {
  const base = typeof m.rpm === "string" && m.rpm.includes("3500") ? 72 : 84;
  return Math.max(0, Math.min(100, base - idx * 7));
}

export default function DiagnosticoPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [motors, setMotors] = useState<MotorRecord[]>([]);
  const [running, setRunning] = useState(false);
  const [diagTotal, setDiagTotal] = useState(0);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      const session = await requireSession(router);
      if (!session) return;
      try {
        const [mePayload, motorsPayload, diagPayload] = await Promise.all([
          apiFetch<MeResponse>("/auth/me", session.access_token),
          apiFetch<MotorListResponse>("/motors?limit=12", session.access_token),
          apiFetch<DiagnosticListResponse>("/diagnostics?limit=50", session.access_token),
        ]);
        setMe(mePayload);
        setMotors(motorsPayload.items || []);
        setDiagTotal(diagPayload.total || (diagPayload.items || []).length);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Falha ao carregar diagnóstico.";
        setError(msg);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  const isAdmin = Boolean(me?.profile?.is_admin);
  const items = useMemo(() => (motors || []).slice(0, 8), [motors]);

  if (loading) return <div className="center-screen text-muted">Carregando diagnóstico...</div>;
  if (!me) return <div className="center-screen error">{error || "Sessão inválida."}</div>;

  return (
    <AppShell
      title="Diagnóstico"
      subtitle="Análise assistida de condição (UI pronta; backend entra incremental)"
      isAdmin={isAdmin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      {error ? (
        <div className="mt-3 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
          {error}
        </div>
      ) : null}

      {!items.length ? (
        <EmptyState
          title="Sem itens para diagnosticar"
          subtitle="Quando houver motores cadastrados, você verá a fila de diagnósticos aqui."
          icon={<Activity className="w-4 h-4 text-primary" />}
          primaryAction={{ label: "Abrir consulta", href: "/motors" }}
          secondaryAction={me.profile.cadastro_allowed ? { label: "Cadastro / OCR", href: "/cadastro" } : undefined}
        />
      ) : (
        <div className="grid gap-3 lg:grid-cols-3">
          <div className="lg:col-span-2 premium-card-elevated p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-display text-sm tracking-wider">FILA DE DIAGNÓSTICO</div>
                <div className="text-[11px] text-muted-foreground font-tech mt-1">
                  Diagnósticos gerados: <span className="font-mono-tech">{diagTotal}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="badge-premium badge-accent">ASSIST</span>
                <button
                  type="button"
                  disabled={running}
                  onClick={async () => {
                    if (!me) return;
                    setRunning(true);
                    setError("");
                    try {
                      const session = await requireSession(router);
                      if (!session) return;
                      await apiFetch<DiagnosticRunResponse>("/diagnostics/run", session.access_token, {
                        method: "POST",
                        body: JSON.stringify({ limit: 6 }),
                      });
                      const diagPayload = await apiFetch<DiagnosticListResponse>("/diagnostics?limit=50", session.access_token);
                      setDiagTotal(diagPayload.total || (diagPayload.items || []).length);
                    } catch (e) {
                      const msg = e instanceof Error ? e.message : "Falha ao gerar diagnóstico.";
                      setError(msg);
                    } finally {
                      setRunning(false);
                    }
                  }}
                  className="text-[11px] px-3 py-2 rounded-xl border border-primary/25 bg-primary/15 hover:bg-primary/20 text-primary transition-colors disabled:opacity-60"
                >
                  {running ? "Gerando..." : "Gerar diagnóstico"}
                </button>
              </div>
            </div>

            <div className="mt-4 grid gap-2">
              {items.map((m, idx) => {
                const marca = String(m.marca || "Motor");
                const modelo = String(m.modelo || "-");
                const score = scoreFor(m, idx);
                const badge =
                  score >= 85 ? { text: "OK", cls: "badge-premium badge-primary" } : score >= 70 ? { text: "ATENÇÃO", cls: "badge-premium badge-warning" } : { text: "RISCO", cls: "badge-premium badge-warning" };
                return (
                  <div key={String(m.id ?? idx)} className="premium-card p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <div className="font-tech text-sm text-foreground truncate">
                            {marca} {modelo}
                          </div>
                          <span className={badge.cls}>{badge.text}</span>
                        </div>
                        <div className="text-[11px] text-muted-foreground font-tech mt-0.5 truncate">
                          {String(m.potencia || "-")} • {String(m.rpm || "-")}
                        </div>
                      </div>
                      <div className="shrink-0 text-right">
                        <div className="text-[10px] text-muted-foreground font-tech">Score</div>
                        <div className="font-display text-lg tracking-wider">{score}</div>
                      </div>
                    </div>
                    <div className="mt-3 progress-premium">
                      <div className="progress-premium-fill" style={{ width: `${score}%` }} />
                    </div>
                    <div className="mt-3 flex items-center gap-2 flex-wrap">
                      <button className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors">
                        Ver recomendações
                      </button>
                      <button className="text-[11px] px-3 py-2 rounded-xl border border-primary/25 bg-primary/15 hover:bg-primary/20 text-primary transition-colors flex items-center gap-2">
                        <Wrench className="w-3.5 h-3.5" />
                        Abrir checklist
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="premium-card-elevated p-5">
            <div className="font-display text-sm tracking-wider">MODELOS</div>
            <div className="text-[11px] text-muted-foreground font-tech mt-1">Painel de ferramentas (placeholder).</div>

            <div className="mt-4 grid gap-2">
              <div className="premium-card p-4">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] text-muted-foreground font-tech">Análise</div>
                  <FlaskConical className="w-4 h-4 text-primary" />
                </div>
                <div className="mt-2 text-[12px] text-muted-foreground font-tech">
                  Nesta fase, a UI está pronta. O backend de diagnóstico entra incrementalmente via FastAPI.
                </div>
              </div>
              <div className="premium-card p-4">
                <div className="text-[11px] text-muted-foreground font-tech">Status</div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="badge-premium badge-primary">STABLE</span>
                  <span className="text-[10px] text-muted-foreground font-mono-tech">v0</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

