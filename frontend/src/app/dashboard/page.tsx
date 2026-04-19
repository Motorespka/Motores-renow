"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Activity, Cpu, Layers, ShieldCheck } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { QueueItem } from "@/components/dashboard/QueueItem";
import {
  countObservacoesRevisao,
  countOcrOrStructured,
  countRecentSince,
  etaLabel,
  inferOriginBreakdown,
  originPercents,
  pickMotorTitleFromRow,
  rowStage,
} from "@/lib/dashboard-stats";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import {
  DashboardMotorRow,
  fetchDiagnosticsCountSupabase,
  fetchMotorDashboardFromSupabase,
  fetchMotorListFromSupabase,
  shouldFetchMotorsFromSupabase,
} from "@/lib/motors-supabase";
import { MeResponse, MotorListResponse, MotorRecord } from "@/lib/types";

function fmtInt(n: number): string {
  try {
    return new Intl.NumberFormat("pt-BR").format(n);
  } catch {
    return String(n);
  }
}

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
  const [dashRows, setDashRows] = useState<DashboardMotorRow[] | null>(null);
  const [fallbackItems, setFallbackItems] = useState<MotorRecord[]>([]);
  const [diagCount, setDiagCount] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      const session = await requireSession(router);
      if (!session) return;
      try {
        const mePayload = await apiFetch<MeResponse>("/auth/me", session.access_token);
        setMe(mePayload);

        if (shouldFetchMotorsFromSupabase()) {
          const [bundle, dCount] = await Promise.all([
            fetchMotorDashboardFromSupabase(420),
            fetchDiagnosticsCountSupabase(),
          ]);
          setDashRows(bundle ?? []);
          setDiagCount(dCount);
          setFallbackItems([]);
        } else {
          const motorsPayload =
            (await fetchMotorListFromSupabase("", 24)) ?? (await apiFetch<MotorListResponse>("/motors?limit=24", session.access_token));
          setDashRows(null);
          setFallbackItems(motorsPayload.items || []);
          setDiagCount(null);
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Falha ao carregar perfil.";
        setError(msg);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  const rawRows = useMemo(() => (dashRows ?? []).map((r) => r.raw), [dashRows]);

  const stats = useMemo(() => {
    if (dashRows && rawRows.length) {
      const total = rawRows.length;
      const last7 = countRecentSince(rawRows, 7);
      const ocrTotal = countOcrOrStructured(rawRows);
      const review = countObservacoesRevisao(rawRows);
      const origin = inferOriginBreakdown(rawRows);
      const [pOcr, pMan, pHist, pInf] = originPercents(origin);
      return { total, last7, ocrTotal, review, pOcr, pMan, pHist, pInf, originLabel: "CALCULADO" as const };
    }
    const total = fallbackItems.length;
    const last7 = Math.max(0, Math.round(total * 0.15));
    const ocrTotal = Math.max(0, Math.round(total * 0.35));
    return {
      total,
      last7,
      ocrTotal,
      review: 0,
      pOcr: 58,
      pMan: 24,
      pHist: 12,
      pInf: 6,
      originLabel: "MIXED" as const,
    };
  }, [dashRows, rawRows, fallbackItems]);

  const queueSlice = useMemo(() => {
    if (dashRows?.length) {
      return dashRows.slice(0, 6);
    }
    return (fallbackItems || []).slice(0, 6).map((item) => ({
      raw: {} as Record<string, unknown>,
      item,
    }));
  }, [dashRows, fallbackItems]);

  if (loading) {
    return <div className="center-screen text-muted">Carregando dashboard...</div>;
  }

  if (!me) {
    return <div className="center-screen error">{error || "Sessao invalida."}</div>;
  }

  const isAdmin = me.profile.is_admin;
  const diagValue = diagCount == null ? "—" : fmtInt(diagCount);
  const diagDelta = diagCount == null ? "Em migração para API" : "emitidos na base";

  return (
    <AppShell
      title="Visão geral"
      subtitle={`Plano ${me.profile.plan} | Acesso ${me.profile.tier}`}
      isAdmin={isAdmin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Motores cadastrados"
          value={fmtInt(stats.total)}
          delta={`+${fmtInt(stats.last7)} últimos 7d`}
          badge={{ text: "LIVE", variant: "accent" }}
          icon={<Layers className="w-4 h-4 text-primary" />}
        />
        <KpiCard
          label="OCR concluído"
          value={fmtInt(stats.ocrTotal)}
          delta="c/ JSON IA ou ficha técnica"
          badge={{ text: "OCR", variant: "accent" }}
          icon={<Cpu className="w-4 h-4 text-primary" />}
        />
        <KpiCard
          label="Diagnósticos emitidos"
          value={diagValue}
          delta={diagDelta}
          badge={{ text: diagCount == null ? "API" : "DIAG", variant: "primary" }}
          icon={<ShieldCheck className="w-4 h-4 text-primary" />}
        />
        <KpiCard
          label="Cadastros c/ inconsistência"
          value={stats.review ? fmtInt(stats.review) : "—"}
          delta="observações c/ revisão"
          badge={{ text: stats.review ? "REV" : "OK", variant: stats.review ? "warning" : "primary" }}
          icon={<Activity className="w-4 h-4 text-primary" />}
        />
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-3">
        <div className="lg:col-span-2 premium-card-elevated p-5">
          <div className="flex items-center justify-between gap-2">
            <div>
              <div className="font-display text-sm tracking-wider">FILA DE TRABALHO</div>
              <div className="text-[11px] text-muted-foreground font-tech mt-1">
                Motores em análise técnica neste workspace (dados reais quando Supabase directo está activo).
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
            {queueSlice.map((row, idx) => {
              const id = row.item.id ?? row.raw.id ?? row.raw.Id ?? idx;
              const mid = String(id ?? "").trim() || `M-${idx}`;
              if (dashRows?.length && row.raw && Object.keys(row.raw).length) {
                const title = pickMotorTitleFromRow(row.raw);
                const st = rowStage(row.raw);
                const sub = [String(row.item.potencia ?? "-"), String(row.item.rpm ?? "-")].join(" • ");
                const eta = `ETA: ${etaLabel(row.raw)}`;
                return (
                  <QueueItem
                    key={String(id) + String(idx)}
                    id={String(id)}
                    motorId={mid}
                    title={title}
                    subtitle={sub}
                    stageLabel={st.label}
                    stageVariant={st.variant}
                    progressPct={st.pct}
                    eta={eta}
                    cadastroSeq={typeof row.item.cadastro_seq === "number" ? row.item.cadastro_seq : undefined}
                  />
                );
              }
              const t = pickTitle(row.item);
              const stage = stageForIndex(idx);
              return (
                <QueueItem
                  key={String(id) + String(idx)}
                  id={String(id)}
                  title={t.title}
                  subtitle={t.subtitle}
                  stageLabel={stage.label}
                  stageVariant={stage.variant}
                  progressPct={stage.pct}
                  eta={stage.eta}
                  cadastroSeq={typeof row.item.cadastro_seq === "number" ? row.item.cadastro_seq : undefined}
                />
              );
            })}
            {!queueSlice.length ? (
              <div className="premium-card p-4 text-[12px] text-muted-foreground font-tech">
                Sem motores na amostra. Abra a consulta técnica ou cadastre um motor.
              </div>
            ) : null}
          </div>

          <div className="mt-5 premium-card p-4 border border-border/35">
            <div className="font-display text-xs tracking-wider text-foreground">Atividade técnica — últimos 7 dias</div>
            <p className="text-[11px] text-muted-foreground font-tech mt-2 leading-relaxed">
              Resumo simples alinhado ao Streamlit enquanto métricas avançadas forem migrando para a API.
            </p>
            <ul className="mt-2 text-[11px] text-muted-foreground space-y-1 font-tech">
              <li>
                Novos registos (janela carregada): <span className="text-primary font-mono-tech">{fmtInt(stats.last7)}</span>
              </li>
              <li>
                Registos com OCR / ficha técnica: <span className="text-primary font-mono-tech">{fmtInt(stats.ocrTotal)}</span>
              </li>
            </ul>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link
                href="/motors"
                className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 transition-colors"
              >
                Abrir consulta
              </Link>
              {me.profile.cadastro_allowed ? (
                <Link
                  href="/cadastro"
                  className="text-[11px] px-3 py-2 rounded-xl border border-primary/25 bg-primary/10 text-primary hover:bg-primary/15 transition-colors"
                >
                  Novo cadastro / OCR
                </Link>
              ) : null}
              <Link
                href="/diagnostico"
                className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 transition-colors"
              >
                Diagnóstico
              </Link>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="premium-card-elevated p-5">
            <div className="font-display text-sm tracking-wider">AÇÕES RÁPIDAS</div>
            <div className="text-[11px] text-muted-foreground font-tech mt-1">Atalhos com permissão.</div>

            <div className="mt-4 grid gap-2">
              <Link
                className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors"
                href="/motors"
              >
                Consulta técnica
              </Link>
              {me.profile.cadastro_allowed ? (
                <Link
                  className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-muted/30 border border-border/40 text-foreground/90 hover:bg-muted/50 transition-colors"
                  href="/cadastro"
                >
                  Cadastro / OCR
                </Link>
              ) : (
                <div className="w-full h-10 flex items-center justify-center rounded-xl bg-muted/20 border border-border/30 text-muted-foreground text-[12px]">
                  Cadastro bloqueado (permissão)
                </div>
              )}
              {isAdmin ? (
                <Link
                  className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-muted/30 border border-border/40 text-foreground/90 hover:bg-muted/50 transition-colors"
                  href="/admin"
                >
                  Administração
                </Link>
              ) : (
                <div className="w-full h-10 flex items-center justify-center rounded-xl bg-muted/20 border border-border/30 text-muted-foreground text-[12px]">
                  Admin restrito
                </div>
              )}
            </div>
          </div>

          <div className="premium-card-elevated p-5">
            <div className="font-display text-sm tracking-wider">AÇÕES PENDENTES</div>
            <div className="text-[11px] text-muted-foreground font-tech mt-1">
              Painel do Streamlit — contadores serão ligados à API na próxima fase.
            </div>
            <div className="mt-4 grid gap-2">
              {[
                { t: "Cálculos pendentes de conferência", v: "—", c: "text-warning" },
                { t: "OCRs aguardando revisão", v: "—", c: "text-primary" },
                { t: "Inconsistências detectadas", v: stats.review ? String(stats.review) : "—", c: "text-destructive" },
                { t: "Laudos em redação", v: "—", c: "text-accent" },
              ].map((x) => (
                <div key={x.t} className="premium-card p-3 bg-muted/10 border border-border/30">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-semibold text-foreground/90 leading-snug">{x.t}</span>
                    <span className={`font-mono-tech text-sm font-bold ${x.c}`}>{x.v}</span>
                  </div>
                </div>
              ))}
            </div>
            {isAdmin ? (
              <p className="mt-3 text-[10px] text-muted-foreground/80 font-tech">Admin: estes itens serão alimentados pela API conforme migração.</p>
            ) : null}
          </div>

          <div className="premium-card p-4">
            <div className="flex items-center justify-between">
              <div className="text-[11px] text-muted-foreground tracking-wide font-tech">Origem dos dados</div>
              <span className="badge-premium badge-primary">{stats.originLabel}</span>
            </div>
            <p className="text-[10px] text-muted-foreground/80 font-tech mt-1 mb-3">
              Distribuição heurística na amostra carregada (OCR / Manual / Histórico / Inferido).
            </p>
            {(
              [
                { k: "OCR", pct: stats.pOcr },
                { k: "Manual", pct: stats.pMan },
                { k: "Histórico", pct: stats.pHist },
                { k: "Inferido", pct: stats.pInf },
              ] as const
            ).map((row) => (
              <div key={row.k} className="mt-2">
                <div className="flex items-center justify-between text-[11px] font-tech text-muted-foreground">
                  <span>{row.k}</span>
                  <span className="font-mono-tech">{row.pct}%</span>
                </div>
                <div className="progress-premium mt-1">
                  <div className="progress-premium-fill" style={{ width: `${Math.max(0, Math.min(100, row.pct))}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
