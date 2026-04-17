"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ClipboardCheck, FileText, ScanLine } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { EmptyState } from "@/components/EmptyState";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { ConferenceListResponse, MeResponse, MotorListResponse, MotorRecord } from "@/lib/types";

function confidenceFor(m: MotorRecord, idx: number): number {
  const base = typeof m.marca === "string" && m.marca.toLowerCase().includes("weg") ? 92 : 86;
  return Math.max(55, Math.min(98, base - idx * 4));
}

export default function ConferenciaPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [motors, setMotors] = useState<MotorRecord[]>([]);
  const [pending, setPending] = useState(0);
  const [busyMotorId, setBusyMotorId] = useState<string>("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      const session = await requireSession(router);
      if (!session) return;
      try {
        const [mePayload, motorsPayload, confPayload] = await Promise.all([
          apiFetch<MeResponse>("/auth/me", session.access_token),
          apiFetch<MotorListResponse>("/motors?limit=12", session.access_token),
          apiFetch<ConferenceListResponse>("/conferences?status=pending&limit=50", session.access_token),
        ]);
        setMe(mePayload);
        setMotors(motorsPayload.items || []);
        setPending(confPayload.total || (confPayload.items || []).length);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Falha ao carregar conferência.";
        setError(msg);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  const isAdmin = Boolean(me?.profile?.is_admin);
  const items = useMemo(() => (motors || []).slice(0, 6), [motors]);

  if (loading) return <div className="center-screen text-muted">Carregando conferência...</div>;
  if (!me) return <div className="center-screen error">{error || "Sessão inválida."}</div>;

  return (
    <AppShell
      title="Conferência Técnica"
      subtitle="Checklist de validação (placa/OCR vs dados normalizados)"
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
          title="Sem itens para conferência"
          subtitle="Quando houver leituras OCR/cadastros recentes, eles aparecem aqui para validação rápida."
          icon={<ClipboardCheck className="w-4 h-4 text-primary" />}
          primaryAction={{ label: "Abrir consulta", href: "/motors" }}
          secondaryAction={me.profile.cadastro_allowed ? { label: "Cadastro / OCR", href: "/cadastro" } : undefined}
        />
      ) : (
        <div className="grid gap-3 lg:grid-cols-3">
          <div className="lg:col-span-2 premium-card-elevated p-5">
            <div className="flex items-center justify-between gap-2">
              <div>
                <div className="font-display text-sm tracking-wider">ITENS PARA CONFERIR</div>
                <div className="text-[11px] text-muted-foreground font-tech mt-1">
                  Pendentes: <span className="font-mono-tech">{pending}</span>
                </div>
              </div>
              <span className="badge-premium badge-accent">QA</span>
            </div>

            <div className="mt-4 grid gap-2">
              {items.map((m, idx) => {
                const marca = String(m.marca || "Motor");
                const modelo = String(m.modelo || "-");
                const conf = confidenceFor(m, idx);
                return (
                  <div key={String(m.id ?? idx)} className="premium-card p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <div className="font-tech text-sm text-foreground truncate">
                            {marca} {modelo}
                          </div>
                          <span className="badge-premium badge-primary">OCR</span>
                        </div>
                        <div className="text-[11px] text-muted-foreground font-tech mt-0.5 truncate">
                          {String(m.potencia || "-")} • {String(m.rpm || "-")}
                        </div>
                      </div>
                      <div className="shrink-0 text-right">
                        <div className="text-[10px] text-muted-foreground font-tech">Confiança</div>
                        <div className="font-display text-lg tracking-wider">{conf}%</div>
                      </div>
                    </div>

                    <div className="mt-3 grid gap-2 md:grid-cols-2">
                      <div className="premium-card p-3">
                        <div className="flex items-center justify-between">
                          <div className="text-[11px] text-muted-foreground font-tech">Placa</div>
                          <ScanLine className="w-4 h-4 text-primary" />
                        </div>
                        <div className="mt-1 text-[12px] text-foreground font-tech">
                          {marca} • {String(m.potencia || "-")}
                        </div>
                      </div>
                      <div className="premium-card p-3">
                        <div className="flex items-center justify-between">
                          <div className="text-[11px] text-muted-foreground font-tech">Normalizado</div>
                          <FileText className="w-4 h-4 text-primary" />
                        </div>
                        <div className="mt-1 text-[12px] text-foreground font-tech">
                          {modelo} • {String(m.rpm || "-")}
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 flex items-center gap-2 flex-wrap">
                      <button className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors">
                        Ver diferenças
                      </button>
                      <button className="text-[11px] px-3 py-2 rounded-xl border border-primary/25 bg-primary/15 hover:bg-primary/20 text-primary transition-colors flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Aprovar
                      </button>
                      <button
                        disabled={busyMotorId === String(m.id ?? "")}
                        onClick={async () => {
                          const motorId = String(m.id ?? "");
                          if (!motorId) return;
                          setBusyMotorId(motorId);
                          setError("");
                          try {
                            const session = await requireSession(router);
                            if (!session) return;
                            await apiFetch<{ ok: boolean; record: unknown }>(
                              `/conferences/${encodeURIComponent(motorId)}/diff`,
                              session.access_token,
                              { method: "POST" }
                            );
                            await apiFetch<{ ok: boolean; record: unknown }>(
                              `/conferences/${encodeURIComponent(motorId)}/decision`,
                              session.access_token,
                              { method: "POST", body: JSON.stringify({ approved: true, reason: "ok", notes: "" }) }
                            );
                            const confPayload = await apiFetch<ConferenceListResponse>(
                              "/conferences?status=pending&limit=50",
                              session.access_token
                            );
                            setPending(confPayload.total || (confPayload.items || []).length);
                          } catch (e) {
                            const msg = e instanceof Error ? e.message : "Falha na conferência.";
                            setError(msg);
                          } finally {
                            setBusyMotorId("");
                          }
                        }}
                        className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-60"
                      >
                        {busyMotorId === String(m.id ?? "") ? "Processando..." : "Gerar diff + aprovar"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="premium-card-elevated p-5">
            <div className="font-display text-sm tracking-wider">POLÍTICA</div>
            <div className="text-[11px] text-muted-foreground font-tech mt-1">Regras de conferência (placeholder).</div>

            <div className="mt-4 grid gap-2">
              <div className="premium-card p-4">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] text-muted-foreground font-tech">Critérios</div>
                  <ClipboardCheck className="w-4 h-4 text-primary" />
                </div>
                <div className="mt-2 text-[12px] text-muted-foreground font-tech">
                  Campo obrigatório, faixa plausível e consistência entre OCR e cadastro manual.
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

