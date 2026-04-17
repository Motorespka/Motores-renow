"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Activity, Cpu, Layers, ShieldCheck } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { QueueItem } from "@/components/dashboard/QueueItem";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { MeResponse, MotorListResponse, MotorRecord } from "@/lib/types";

function pickTitle(m: MotorRecord): { title: string; subtitle: string } {
  const marca = String(m.marca || "Motor");
  const modelo = String(m.modelo || "-");
  const potencia = String(m.potencia || "-");
  const rpm = String(m.rpm || "-");
  return { title: `${marca} ${modelo}`.trim(), subtitle: `${potencia} • ${rpm}` };
}

function stageForIndex(idx: number): { label: string; variant: "primary" | "accent" | "warning"; pct: number; eta: string } {
  const stages = [
    { label: "OCR", variant: "accent" as const, pct: 28, eta: "ETA ~ 3m" },
    { label: "VALIDAÇÃO", variant: "primary" as const, pct: 54, eta: "ETA ~ 8m" },
    { label: "DIAGNÓSTICO", variant: "warning" as const, pct: 76, eta: "ETA ~ 12m" },
    { label: "PRONTO", variant: "primary" as const, pct: 100, eta: "OK" },
  ];
  return stages[idx % stages.length];
}

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [motors, setMotors] = useState<MotorRecord[]>([]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      const session = await requireSession(router);
      if (!session) return;
      try {
        const [mePayload, motorsPayload] = await Promise.all([
          apiFetch<MeResponse>("/auth/me", session.access_token),
          apiFetch<MotorListResponse>("/motors?limit=6", session.access_token),
        ]);
        setMe(mePayload);
        setMotors(motorsPayload.items || []);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Falha ao carregar perfil.";
        setError(msg);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  if (loading) {
    return <div className="center-screen text-muted">Carregando dashboard...</div>;
  }

  if (!me) {
    return <div className="center-screen error">{error || "Sessao invalida."}</div>;
  }

  const isAdmin = me.profile.is_admin;
  const motorTotal = motors.length;
  const ocrCount = Math.max(0, Math.round(motorTotal * 0.35));
  return (
    <AppShell
      title="Dashboard"
      subtitle={`Plano ${me.profile.plan} | Acesso ${me.profile.tier}`}
      isAdmin={isAdmin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Motores monitorados"
          value={String(motorTotal)}
          delta="+ hoje"
          badge={{ text: "LIVE", variant: "accent" }}
          icon={<Layers className="w-4 h-4 text-primary" />}
        />
        <KpiCard
          label="OCR em processamento"
          value={String(ocrCount)}
          delta="fila ativa"
          badge={{ text: "OCR", variant: "accent" }}
          icon={<Cpu className="w-4 h-4 text-primary" />}
        />
        <KpiCard
          label="Conta"
          value={me.profile.ativo ? "Ativa" : "Inativa"}
          delta={me.profile.role || "user"}
          badge={{ text: me.profile.plan.toUpperCase(), variant: "primary" }}
          icon={<ShieldCheck className="w-4 h-4 text-primary" />}
        />
        <KpiCard
          label="Sinal do sistema"
          value="OK"
          delta="sem incidentes"
          badge={{ text: "STABLE", variant: "primary" }}
          icon={<Activity className="w-4 h-4 text-primary" />}
        />
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-3">
        <div className="lg:col-span-2 premium-card-elevated p-5">
          <div className="flex items-center justify-between gap-2">
            <div>
              <div className="font-display text-sm tracking-wider">FILA DE TRABALHO</div>
              <div className="text-[11px] text-muted-foreground font-tech mt-1">
                Recentes e em processamento (fallback DEV no localhost).
              </div>
            </div>
            <Link
              href="/motors"
              className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors"
            >
              Ver consulta
            </Link>
          </div>

          <div className="mt-4 grid gap-3">
            {(motors || []).slice(0, 4).map((m, idx) => {
              const t = pickTitle(m);
              const stage = stageForIndex(idx);
              return (
                <QueueItem
                  key={String(m.id ?? idx)}
                  id={String(m.id ?? idx)}
                  title={t.title}
                  subtitle={t.subtitle}
                  stageLabel={stage.label}
                  stageVariant={stage.variant}
                  progressPct={stage.pct}
                  eta={stage.eta}
                />
              );
            })}
            {!motors.length ? (
              <div className="premium-card p-4 text-[12px] text-muted-foreground font-tech">
                Sem itens ainda. Assim que o backend estiver conectado, esta seção mostra a fila real.
              </div>
            ) : null}
          </div>
        </div>

        <div className="premium-card-elevated p-5">
          <div className="font-display text-sm tracking-wider">AÇÕES RÁPIDAS</div>
          <div className="text-[11px] text-muted-foreground font-tech mt-1">Atalhos com permissão e fallback.</div>

          <div className="mt-4 grid gap-2">
            <Link className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors" href="/motors">
              Consulta técnica
            </Link>
            {me.profile.cadastro_allowed ? (
              <Link className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-muted/30 border border-border/40 text-foreground/90 hover:bg-muted/50 transition-colors" href="/cadastro">
                Cadastro / OCR
              </Link>
            ) : (
              <div className="w-full h-10 flex items-center justify-center rounded-xl bg-muted/20 border border-border/30 text-muted-foreground text-[12px]">
                Cadastro bloqueado (permissão)
              </div>
            )}
            {isAdmin ? (
              <Link className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-muted/30 border border-border/40 text-foreground/90 hover:bg-muted/50 transition-colors" href="/admin">
                Administração
              </Link>
            ) : (
              <div className="w-full h-10 flex items-center justify-center rounded-xl bg-muted/20 border border-border/30 text-muted-foreground text-[12px]">
                Admin restrito
              </div>
            )}
          </div>

          <div className="mt-5 premium-card p-4">
            <div className="flex items-center justify-between">
              <div className="text-[11px] text-muted-foreground tracking-wide font-tech">Origem dos dados</div>
              <span className="badge-premium badge-primary">MIXED</span>
            </div>
            <div className="mt-3 grid gap-2">
              <div className="flex items-center justify-between text-[11px] font-tech text-muted-foreground">
                <span>OCR</span>
                <span className="font-mono-tech">62%</span>
              </div>
              <div className="progress-premium">
                <div className="progress-premium-fill" style={{ width: "62%" }} />
              </div>
              <div className="flex items-center justify-between text-[11px] font-tech text-muted-foreground">
                <span>Manual</span>
                <span className="font-mono-tech">28%</span>
              </div>
              <div className="progress-premium">
                <div className="progress-premium-fill" style={{ width: "28%" }} />
              </div>
              <div className="flex items-center justify-between text-[11px] font-tech text-muted-foreground">
                <span>Import</span>
                <span className="font-mono-tech">10%</span>
              </div>
              <div className="progress-premium">
                <div className="progress-premium-fill" style={{ width: "10%" }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
